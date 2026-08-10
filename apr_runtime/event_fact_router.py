from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from .event_ledger import NativeEvent
from .need_graph import PerceptualNeedGraph
from .world_state import WorldState


@dataclass(frozen=True)
class EventFactRule:
    fact_keys: tuple[str, ...]
    kind_prefix: Optional[str] = None
    target_prefix: Optional[str] = None
    source: Optional[str] = None
    weight: float = 1.0

    def matches(self, event: NativeEvent) -> bool:
        if self.source is not None and event.source != self.source:
            return False
        if self.kind_prefix is not None and not event.kind.startswith(self.kind_prefix):
            return False
        if self.target_prefix is not None and not event.target.startswith(self.target_prefix):
            return False
        return True


class EventFactDependencyMap:
    """Maps low-level/runtime events to WorldState facts they may invalidate."""

    def __init__(self, rules: Optional[Iterable[EventFactRule]] = None) -> None:
        self.rules: List[EventFactRule] = list(rules or [])

    def add(self, rule: EventFactRule) -> None:
        self.rules.append(rule)

    def affected_facts(self, event: NativeEvent) -> Dict[str, float]:
        out: Dict[str, float] = {}
        explicit = event.payload.get("affected_facts")
        if isinstance(explicit, dict):
            for key, weight in explicit.items():
                out[str(key)] = max(out.get(str(key), 0.0), float(weight))
        elif isinstance(explicit, (list, tuple, set)):
            for key in explicit:
                out[str(key)] = max(out.get(str(key), 0.0), 1.0)

        for rule in self.rules:
            if not rule.matches(event):
                continue
            for fact in rule.fact_keys:
                out[fact] = max(out.get(fact, 0.0), float(rule.weight))
        return out


@dataclass
class TaskAwareRoutingConfig:
    need_boost: float = 0.85
    unrelated_discount: float = 0.82
    critical_floor: float = 0.85
    preserve_critical: bool = True


@dataclass(frozen=True)
class TaskAwareRoute:
    original: NativeEvent
    routed: NativeEvent
    affected_facts: Dict[str, float]
    need_relevance: float


class TaskAwareEventRouter:
    """Reweights events using current task information needs.

    Raw significance is retained in payload. Critical events are never reduced.
    """

    def __init__(
        self,
        world: WorldState,
        needs: PerceptualNeedGraph,
        dependencies: EventFactDependencyMap,
        *,
        config: Optional[TaskAwareRoutingConfig] = None,
    ) -> None:
        self.world = world
        self.needs = needs
        self.dependencies = dependencies
        self.config = config or TaskAwareRoutingConfig()

    def route(self, event: NativeEvent) -> TaskAwareRoute:
        affected = self.dependencies.affected_facts(event)
        explicit_urgency = event.payload.get("apr_explicit_need_urgency", 0.0)
        try:
            relevance = max(0.0, min(1.0, float(explicit_urgency)))
        except (TypeError, ValueError):
            relevance = 0.0
        for fact_key, edge_weight in affected.items():
            relevance = max(
                relevance,
                self.needs.urgency_for_fact(fact_key, self.world) * max(0.0, edge_weight),
            )
        relevance = max(0.0, min(1.0, relevance))

        base = max(0.0, min(1.0, float(event.significance)))
        if relevance > 0:
            adjusted = base + (1.0 - base) * relevance * self.config.need_boost
        else:
            adjusted = base * self.config.unrelated_discount

        if self.config.preserve_critical and base >= self.config.critical_floor:
            adjusted = max(adjusted, base)

        adjusted = max(0.0, min(1.0, adjusted))
        payload = {
            **event.payload,
            "apr_task_aware": True,
            "apr_original_event_id": event.id,
            "apr_original_significance": base,
            "apr_need_relevance": relevance,
            "apr_affected_facts": affected,
        }
        routed = NativeEvent(
            kind=event.kind,
            source=event.source,
            target=event.target,
            significance=adjusted,
            timestamp=event.timestamp,
            node_id=event.node_id,
            backend_node_id=event.backend_node_id,
            hwnd=event.hwnd,
            payload=payload,
            id=event.id,
        )
        return TaskAwareRoute(
            original=event,
            routed=routed,
            affected_facts=affected,
            need_relevance=relevance,
        )
