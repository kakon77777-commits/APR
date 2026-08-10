from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

from .scheduler import ScheduledEvent, UnifiedEventScheduler

Handler = Callable[[ScheduledEvent], Any]
Predicate = Callable[[ScheduledEvent], bool]


@dataclass
class ExecutionResult:
    item: ScheduledEvent
    ok: bool
    result: Any = None
    error: Optional[str] = None
    elapsed: float = 0.0


class EventHandlerRegistry:
    def __init__(self) -> None:
        self._handlers: List[Tuple[Predicate, Handler]] = []

    def register(self, predicate: Predicate, handler: Handler) -> None:
        self._handlers.append((predicate, handler))

    def register_kind(self, kind: str, handler: Handler) -> None:
        self.register(lambda item, k=kind: item.event.kind == k, handler)

    def register_prefix(self, prefix: str, handler: Handler) -> None:
        self.register(lambda item, p=prefix: item.event.kind.startswith(p), handler)

    def resolve(self, item: ScheduledEvent) -> Optional[Handler]:
        for predicate, handler in self._handlers:
            if predicate(item):
                return handler
        return None


class AsyncEventExecutor:
    """Bounded-concurrency executor for scheduler work."""

    def __init__(
        self,
        registry: EventHandlerRegistry,
        *,
        max_concurrency: int = 4,
        timeout: float = 30.0,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        self.registry = registry
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self._sem = asyncio.Semaphore(max_concurrency)

    async def _invoke(self, handler: Handler, item: ScheduledEvent) -> Any:
        value = handler(item)
        if inspect.isawaitable(value):
            return await value
        return value

    async def _run_one(self, item: ScheduledEvent) -> ExecutionResult:
        start = time.perf_counter()
        handler = self.registry.resolve(item)
        if handler is None:
            return ExecutionResult(
                item=item,
                ok=False,
                error="no_handler",
                elapsed=time.perf_counter() - start,
            )
        try:
            async with self._sem:
                result = await asyncio.wait_for(self._invoke(handler, item), timeout=self.timeout)
            return ExecutionResult(
                item=item,
                ok=True,
                result=result,
                elapsed=time.perf_counter() - start,
            )
        except Exception as exc:
            return ExecutionResult(
                item=item,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                elapsed=time.perf_counter() - start,
            )

    async def execute(self, items: List[ScheduledEvent]) -> List[ExecutionResult]:
        if not items:
            return []
        return await asyncio.gather(*(self._run_one(item) for item in items))


class AsyncSchedulerRuntime:
    """Convenience loop: refresh -> pop -> execute."""

    def __init__(self, scheduler: UnifiedEventScheduler, executor: AsyncEventExecutor) -> None:
        self.scheduler = scheduler
        self.executor = executor

    async def tick(
        self, *, max_items: int = 16, now: Optional[float] = None
    ) -> List[ExecutionResult]:
        self.scheduler.emit_due_refreshes(now=now)
        batch = self.scheduler.pop_batch(max_items=max_items, now=now)
        return await self.executor.execute(batch)
