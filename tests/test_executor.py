import asyncio
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    AsyncEventExecutor,
    EventHandlerRegistry,
    NativeEvent,
    UnifiedEventScheduler,
)


class ExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_async_handlers_execute(self):
        scheduler = UnifiedEventScheduler()
        for i in range(3):
            scheduler.ingest(
                NativeEvent(
                    kind="work.item",
                    source="test",
                    target=str(i),
                    significance=0.5,
                ),
                persist=False,
            )
        batch = scheduler.pop_batch(max_items=3)

        registry = EventHandlerRegistry()

        async def handler(item):
            await asyncio.sleep(0.001)
            return "done:" + item.event.target

        registry.register_prefix("work.", handler)

        executor = AsyncEventExecutor(registry, max_concurrency=2)
        results = await executor.execute(batch)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.ok for r in results))
        self.assertEqual({r.result for r in results}, {"done:0", "done:1", "done:2"})

    async def test_missing_handler_is_reported_not_raised(self):
        scheduler = UnifiedEventScheduler()
        scheduler.ingest(
            NativeEvent(kind="unknown", source="test", target="x", significance=0.5),
            persist=False,
        )
        item = scheduler.pop_batch(max_items=1)[0]
        executor = AsyncEventExecutor(EventHandlerRegistry())
        result = (await executor.execute([item]))[0]
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "no_handler")


if __name__ == "__main__":
    unittest.main()
