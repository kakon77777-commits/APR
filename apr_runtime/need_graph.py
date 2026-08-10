from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from .models import FactStatus
from .world_state import WorldState


class NeedState(str, Enum):
    SATISFIED = "satisfied"
    UNKNOWN = "unknown"
    STALE = "stale"
    UNCERTAIN = "uncertain"
    CONTRADICTED = "contradicted"
    BLOCKED = "blocked"


@dataclass
class PerceptualNeed:
    id: str
    fact_key: str
    description: str = ""
    min_confidence: float = 0.8
    risk: float = 0.2
    weight: float = 1.0
    mandatory: bool = True
    dependencies: Set[str] = field(default_factory=set)
    refresh_interval: Optional[float] = None


@dataclass(frozen=True)
class NeedAssessment:
    need_id: str
    fact_key: str
    state: NeedState
    confidence: float
    urgency: float
    reason: str
    blocked_by: tuple[str, ...] = ()


class PerceptualNeedGraph:
    """Task-facing graph of facts the agent must know well enough to act.

    Nodes are information requirements, not world entities. Dependencies encode
    information prerequisites, e.g. `download.ready` may depend on both
    `browser.download.state` and `file.exists`.
    """

    def __init__(self) -> None:
        self.needs: Dict[str, PerceptualNeed] = {}
        self._fact_to_needs: Dict[str, Set[str]] = {}

    def add_need(self, need: PerceptualNeed) -> None:
        if need.id in self.needs:
            raise ValueError(f"Duplicate need id: {need.id}")
        self.needs[need.id] = need
        self._fact_to_needs.setdefault(need.fact_key, set()).add(need.id)

    def add_dependency(self, need_id: str, prerequisite_need_id: str) -> None:
        if need_id not in self.needs or prerequisite_need_id not in self.needs:
            raise KeyError("Both need and prerequisite must exist first.")
        if need_id == prerequisite_need_id:
            raise ValueError("A need cannot depend on itself.")
        self.needs[need_id].dependencies.add(prerequisite_need_id)
        try:
            self._assert_acyclic()
        except Exception:
            self.needs[need_id].dependencies.discard(prerequisite_need_id)
            raise

    def _assert_acyclic(self) -> None:
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                raise ValueError("PerceptualNeedGraph dependency cycle detected.")
            visiting.add(node)
            for dep in self.needs[node].dependencies:
                visit(dep)
            visiting.remove(node)
            visited.add(node)

        for node in self.needs:
            visit(node)

    @staticmethod
    def _state_from_fact(status: FactStatus) -> NeedState:
        return {
            FactStatus.KNOWN: NeedState.SATISFIED,
            FactStatus.UNKNOWN: NeedState.UNKNOWN,
            FactStatus.STALE: NeedState.STALE,
            FactStatus.UNCERTAIN: NeedState.UNCERTAIN,
            FactStatus.CONTRADICTED: NeedState.CONTRADICTED,
        }[status]

    @staticmethod
    def _deficiency(state: NeedState, confidence: float, min_conf: float) -> float:
        if state == NeedState.CONTRADICTED:
            return 1.0
        if state == NeedState.UNKNOWN:
            return 0.95
        if state == NeedState.STALE:
            return 0.85
        if state == NeedState.UNCERTAIN:
            return 0.75
        if state == NeedState.BLOCKED:
            return 0.65
        if confidence >= min_conf:
            return 0.0
        return min(1.0, 0.35 + (min_conf - confidence))

    def assess(self, need_id: str, world: WorldState) -> NeedAssessment:
        need = self.needs[need_id]
        blocked = []
        for dep_id in sorted(need.dependencies):
            dep = self.assess(dep_id, world)
            if dep.state != NeedState.SATISFIED:
                blocked.append(dep_id)

        fact = world.get(need.fact_key)
        state = self._state_from_fact(fact.status)
        if state == NeedState.SATISFIED and fact.confidence < need.min_confidence:
            state = NeedState.UNCERTAIN

        if blocked:
            state = NeedState.BLOCKED

        deficiency = self._deficiency(state, fact.confidence, need.min_confidence)
        # Risk and task weight raise urgency but never make satisfied needs urgent.
        urgency = (
            0.0
            if deficiency == 0
            else min(
                1.0,
                deficiency * (0.65 + 0.35 * max(0.0, min(1.0, need.risk))) * max(0.1, need.weight),
            )
        )

        if blocked:
            reason = "Blocked by unsatisfied prerequisite information."
        elif state == NeedState.SATISFIED:
            reason = "Required fact is fresh and sufficiently confident."
        else:
            reason = f"Required fact is {state.value}."

        return NeedAssessment(
            need_id=need.id,
            fact_key=need.fact_key,
            state=state,
            confidence=fact.confidence,
            urgency=urgency,
            reason=reason,
            blocked_by=tuple(blocked),
        )

    def assessments(self, world: WorldState) -> List[NeedAssessment]:
        return [self.assess(need_id, world) for need_id in self.needs]

    def needs_for_fact(self, fact_key: str) -> List[PerceptualNeed]:
        return [self.needs[n] for n in sorted(self._fact_to_needs.get(fact_key, set()))]

    def urgency_for_fact(self, fact_key: str, world: WorldState) -> float:
        values = [self.assess(n.id, world).urgency for n in self.needs_for_fact(fact_key)]
        return max(values, default=0.0)

    def ready(self, world: WorldState) -> bool:
        for need in self.needs.values():
            if need.mandatory and self.assess(need.id, world).state != NeedState.SATISFIED:
                return False
        return True

    def frontier(self, world: WorldState) -> List[NeedAssessment]:
        """Return unsatisfied, currently actionable needs ordered by urgency."""
        items = [
            self.assess(n.id, world)
            for n in self.needs.values()
            if self.assess(n.id, world).state not in (NeedState.SATISFIED, NeedState.BLOCKED)
        ]
        return sorted(items, key=lambda item: item.urgency, reverse=True)
