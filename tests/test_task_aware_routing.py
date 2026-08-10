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
    WorldState,
)


class TaskAwareRoutingTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(EvidenceStore())
        self.graph = PerceptualNeedGraph()
        self.graph.add_need(PerceptualNeed("warn", "desktop.warning.visible", risk=0.95))
        deps = EventFactDependencyMap(
            [
                EventFactRule(
                    ("desktop.warning.visible",),
                    kind_prefix="DOM.childNode",
                    weight=1.0,
                )
            ]
        )
        self.router = TaskAwareEventRouter(self.world, self.graph, deps)

    def test_relevant_event_is_boosted(self):
        ev = NativeEvent(
            "DOM.childNodeInserted",
            "browser_cdp",
            "browser.dom.node:1",
            0.4,
        )
        route = self.router.route(ev)
        self.assertGreater(route.routed.significance, ev.significance)
        self.assertGreater(route.need_relevance, 0.7)
        self.assertIn("desktop.warning.visible", route.affected_facts)

    def test_unrelated_event_is_downweighted(self):
        ev = NativeEvent("mouse.move", "screen_delta", "desktop.pointer", 0.4)
        route = self.router.route(ev)
        self.assertLess(route.routed.significance, ev.significance)

    def test_critical_unrelated_event_is_not_downweighted(self):
        ev = NativeEvent("safety.alarm", "semantic", "machine.alarm", 0.95)
        route = self.router.route(ev)
        self.assertGreaterEqual(route.routed.significance, 0.95)


if __name__ == "__main__":
    unittest.main()
