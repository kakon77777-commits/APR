from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .event_ledger import EventLedger, NativeEvent
from .models import Evidence, Modality
from .world_state import WorldState


@dataclass
class VerifiedEvent:
    event: NativeEvent
    verified: bool
    state_key: Optional[str]
    state_value: Any = None
    metadata: Optional[Dict[str, Any]] = None


class EventNativeRuntime:
    """Native events are ledger entries; only targeted verification writes WorldState."""

    def __init__(self, world: WorldState, ledger: EventLedger) -> None:
        self.world = world
        self.ledger = ledger

    def record(self, event: NativeEvent) -> None:
        self.ledger.append(event)

    def write_verified_state(
        self,
        event: NativeEvent,
        *,
        key: str,
        value: Any,
        confidence: float,
        source: str,
        volatile: bool = True,
        ttl: float = 3.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Evidence:
        self.world.configure_fact(key, volatile=volatile, ttl=ttl)
        evidence = Evidence(
            claim_key=key,
            observed_value=value,
            modality=Modality.STRUCTURED,
            source=source,
            confidence=confidence,
            cost=0.0,
            metadata={
                "native_event_id": event.id,
                "native_event_kind": event.kind,
                **(metadata or {}),
            },
        )
        self.world.revise(evidence)
        return evidence
