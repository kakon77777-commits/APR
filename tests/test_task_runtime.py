import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    EventFactDependencyMap,
    EventFactRule,
    EvidenceStore,
    NativeEvent,
    PerceptualNeed,
    PerceptualNeedGraph,
    TaskAwareEventRouter,
    TaskAwarePerceptionRuntime,
    UnifiedEventRuntime,
    UnifiedEventScheduler,
    WorldState,
)


class TaskRuntimeTests(unittest.TestCase):
    def test_task_relevant_event_dispatches_ahead_of_unrelated_event(self):
        world = WorldState(EvidenceStore())
        graph = PerceptualNeedGraph()
        graph.add_need(PerceptualNeed("need", "download.failed", risk=0.95))
        deps = EventFactDependencyMap(
            [
                EventFactRule(
                    ("download.failed",),
                    kind_prefix="browser_dom_changed",
                )
            ]
        )
        router = TaskAwareEventRouter(world, graph, deps)
        scheduler = UnifiedEventScheduler()
        runtime = TaskAwarePerceptionRuntime(UnifiedEventRuntime(scheduler), router)
        relevant = NativeEvent(
            "browser_dom_changed",
            "browser_native_state",
            "browser.dom",
            0.35,
        )
        unrelated = NativeEvent(
            "pointer.motion",
            "screen_delta",
            "desktop.pointer",
            0.55,
        )
        report = runtime.submit_native([unrelated, relevant], persist=False, now=1.0)
        self.assertEqual(report.routed, 2)
        batch = scheduler.pop_batch(max_items=2, now=1.1)
        self.assertEqual(batch[0].event.kind, "browser_dom_changed")

    def test_raw_event_history_keeps_original_significance(self):
        import tempfile

        from apr_runtime import EventLedger

        with tempfile.TemporaryDirectory() as tmp:
            world = WorldState(EvidenceStore())
            graph = PerceptualNeedGraph()
            graph.add_need(PerceptualNeed("need", "critical.fact", risk=0.95))
            deps = EventFactDependencyMap(
                [
                    EventFactRule(("critical.fact",), kind_prefix="small.change"),
                ]
            )
            router = TaskAwareEventRouter(world, graph, deps)
            ledger = EventLedger(Path(tmp) / "events.sqlite3")
            scheduler = UnifiedEventScheduler(ledger=ledger)
            runtime = TaskAwarePerceptionRuntime(UnifiedEventRuntime(scheduler), router)
            event = NativeEvent("small.change", "browser_cdp", "browser.dom.node:7", 0.2)
            runtime.submit_native([event], persist=True, now=1.0)

            row = ledger.recent(limit=1)[0]
            self.assertAlmostEqual(row["significance"], 0.2)
            queued = scheduler.pending(now=1.0)[0].event
            self.assertGreater(queued.significance, 0.2)
            self.assertEqual(queued.id, event.id)


if __name__ == "__main__":
    unittest.main()
