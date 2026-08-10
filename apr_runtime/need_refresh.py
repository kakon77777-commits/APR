from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

from .event_ledger import NativeEvent
from .need_graph import PerceptualNeedGraph
from .world_state import WorldState


@dataclass
class NeedRefreshConfig:
    source: str = "perceptual_need"
    kind: str = "apr.need.refresh"
    minimum_significance: float = 0.20
    critical_risk: float = 0.80
    critical_floor: float = 0.85


class NeedRefreshPlanner:
    """Turns information deficits into scheduler events."""

    def __init__(
        self,
        world: WorldState,
        needs: PerceptualNeedGraph,
        *,
        config: Optional[NeedRefreshConfig] = None,
    ) -> None:
        self.world = world
        self.needs = needs
        self.config = config or NeedRefreshConfig()

    def emit(self, *, now: Optional[float] = None) -> List[NativeEvent]:
        now = time.time() if now is None else float(now)
        events: List[NativeEvent] = []
        for assessment in self.needs.frontier(self.world):
            need = self.needs.needs[assessment.need_id]
            significance = max(self.config.minimum_significance, assessment.urgency)
            if need.risk >= self.config.critical_risk:
                significance = max(significance, self.config.critical_floor)
            events.append(
                NativeEvent(
                    kind=self.config.kind,
                    source=self.config.source,
                    target=assessment.fact_key,
                    significance=min(1.0, significance),
                    timestamp=now,
                    payload={
                        "need_id": assessment.need_id,
                        "fact_key": assessment.fact_key,
                        "need_state": assessment.state.value,
                        "need_urgency": assessment.urgency,
                        "risk": need.risk,
                        "min_confidence": need.min_confidence,
                        "affected_facts": {assessment.fact_key: 1.0},
                        "reason": assessment.reason,
                    },
                )
            )
        return events
