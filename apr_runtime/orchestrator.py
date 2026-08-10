from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .event_ledger import NativeEvent
from .executor import AsyncSchedulerRuntime, ExecutionResult
from .scheduler import UnifiedEventScheduler
from .stream import StreamEvent


@dataclass
class IngestReport:
    accepted: int = 0
    dropped: int = 0


class UnifiedEventRuntime:
    """One ingress for Browser, Windows, screen-delta, and semantic events."""

    def __init__(
        self,
        scheduler: UnifiedEventScheduler,
        async_runtime: Optional[AsyncSchedulerRuntime] = None,
    ) -> None:
        self.scheduler = scheduler
        self.async_runtime = async_runtime

    def submit_native(
        self,
        events: Iterable[NativeEvent],
        *,
        now: Optional[float] = None,
        persist: bool = True,
    ) -> IngestReport:
        accepted = 0
        total = 0
        for event in events:
            total += 1
            if self.scheduler.ingest(event, now=now, persist=persist):
                accepted += 1
        return IngestReport(accepted=accepted, dropped=total - accepted)

    def submit_stream(
        self,
        events: Iterable[StreamEvent],
        *,
        source: str,
        now: Optional[float] = None,
        persist: bool = True,
    ) -> IngestReport:
        accepted = 0
        total = 0
        for event in events:
            total += 1
            if self.scheduler.ingest_stream(event, source=source, now=now, persist=persist):
                accepted += 1
        return IngestReport(accepted=accepted, dropped=total - accepted)

    async def tick(
        self, *, max_items: int = 16, now: Optional[float] = None
    ) -> List[ExecutionResult]:
        if self.async_runtime is None:
            raise RuntimeError("No AsyncSchedulerRuntime configured.")
        return await self.async_runtime.tick(max_items=max_items, now=now)
