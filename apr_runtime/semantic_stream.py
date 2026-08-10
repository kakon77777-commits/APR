from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .semantic_pipeline import (
    SemanticEvidencePipeline,
    SemanticInspectionRecord,
)
from .stream import RealStreamMonitor, StreamEvent


@dataclass
class SemanticStreamConfig:
    escalation_threshold: float = 0.30
    inspect_screen_changes: bool = True
    max_inspections_per_tick: int = 1


class SemanticStreamRuntime:
    """
    Two-speed APR runtime:
      Fast Loop  -> RealStreamMonitor
      Slow Loop  -> SemanticEvidencePipeline

    Only selected high-significance screen changes are sent to semantic
    inspection. Everything else remains cheap state/event monitoring.
    """

    def __init__(
        self,
        monitor: RealStreamMonitor,
        pipeline: SemanticEvidencePipeline,
        *,
        config: Optional[SemanticStreamConfig] = None,
    ) -> None:
        self.monitor = monitor
        self.pipeline = pipeline
        self.config = config or SemanticStreamConfig()

    def tick(
        self,
        *,
        goal: Optional[str] = None,
    ) -> Tuple[List[StreamEvent], List[SemanticInspectionRecord]]:
        events = self.monitor.poll_once()
        inspections: List[SemanticInspectionRecord] = []

        if not self.config.inspect_screen_changes:
            return events, inspections

        candidates = [
            e
            for e in events
            if e.kind == "screen_change" and e.significance >= self.config.escalation_threshold
        ]
        candidates.sort(key=lambda e: e.significance, reverse=True)

        frame = self.monitor.latest_frame
        if frame is None:
            return events, inspections

        for event in candidates[: self.config.max_inspections_per_tick]:
            inspections.append(
                self.pipeline.inspect_screen_event(
                    event,
                    frame,
                    goal=goal,
                )
            )

        return events, inspections
