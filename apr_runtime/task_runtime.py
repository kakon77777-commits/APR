from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .event_fact_router import TaskAwareEventRouter
from .event_ledger import NativeEvent
from .need_refresh import NeedRefreshPlanner
from .orchestrator import IngestReport, UnifiedEventRuntime


@dataclass
class TaskAwareIngestReport(IngestReport):
    routed: int = 0
    boosted: int = 0
    downweighted: int = 0


class TaskAwarePerceptionRuntime:
    """Task-aware ingress in front of the v0.6 unified scheduler."""

    def __init__(
        self,
        runtime: UnifiedEventRuntime,
        router: TaskAwareEventRouter,
        refresh_planner: Optional[NeedRefreshPlanner] = None,
    ) -> None:
        self.runtime = runtime
        self.router = router
        self.refresh_planner = refresh_planner

    def submit_native(
        self,
        events: Iterable[NativeEvent],
        *,
        now: Optional[float] = None,
        persist: bool = True,
    ) -> TaskAwareIngestReport:
        accepted = dropped = routed_n = boosted = downweighted = 0
        for event in events:
            # Preserve the raw event in the append-only ledger. The routed
            # significance belongs to the transient scheduler work-set, not
            # to historical truth about what the source emitted.
            if persist and self.runtime.scheduler.ledger is not None:
                self.runtime.scheduler.ledger.append(event)

            route = self.router.route(event)
            routed_n += 1
            if route.routed.significance > route.original.significance:
                boosted += 1
            elif route.routed.significance < route.original.significance:
                downweighted += 1
            if self.runtime.scheduler.ingest(route.routed, now=now, persist=False):
                accepted += 1
            else:
                dropped += 1
        return TaskAwareIngestReport(
            accepted=accepted,
            dropped=dropped,
            routed=routed_n,
            boosted=boosted,
            downweighted=downweighted,
        )

    def emit_need_refreshes(
        self,
        *,
        now: Optional[float] = None,
        persist: bool = True,
    ) -> TaskAwareIngestReport:
        if self.refresh_planner is None:
            return TaskAwareIngestReport()
        return self.submit_native(
            self.refresh_planner.emit(now=now),
            now=now,
            persist=persist,
        )
