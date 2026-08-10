import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    APRRuntime,
    BrowserSnapshot,
    BrowserStreamMonitor,
    BrowserStructuredAdapter,
    Budget,
    ChannelProfile,
    EvidenceStore,
    Goal,
    Modality,
    PolicyController,
    ReadingMode,
    WorldState,
)


class FakeBrowser:
    def __init__(self, snapshots):
        self.snapshots = list(snapshots)
        self.i = 0

    def snapshot(self):
        value = self.snapshots[min(self.i, len(self.snapshots) - 1)]
        self.i += 1
        return value


def snap(url, title, aria, dom, count, active=None):
    return BrowserSnapshot(
        url=url,
        title=title,
        aria_snapshot=aria,
        aria_digest=f"aria:{aria}",
        dom_digest=f"dom:{dom}",
        dom_element_count=count,
        active_element=active or {},
    )


class BrowserNativeStateTests(unittest.TestCase):
    def test_browser_monitor_emits_navigation_and_structure_events(self):
        world = WorldState(EvidenceStore())
        source = FakeBrowser(
            [
                snap("https://a", "A", "a", "a", 10, {"tag": "BODY"}),
                snap("https://b", "B", "b", "b", 12, {"tag": "INPUT"}),
            ]
        )
        monitor = BrowserStreamMonitor(world, source)

        self.assertEqual(monitor.poll_once(), [])
        events = monitor.poll_once()
        kinds = {e.kind for e in events}

        self.assertIn("browser_navigation", kinds)
        self.assertIn("browser_aria_changed", kinds)
        self.assertIn("browser_dom_changed", kinds)
        self.assertIn("browser_focus_changed", kinds)
        self.assertEqual(world.get("browser.url").value, "https://b")
        self.assertTrue(world.get("browser.url").volatile)

    def test_browser_adapter_can_satisfy_goal_then_skip(self):
        store = EvidenceStore()
        world = WorldState(store)
        source = FakeBrowser(
            [
                snap("https://a", "A", "a", "a", 10),
                snap("https://a", "A", "a", "a", 10),
            ]
        )
        adapter = BrowserStructuredAdapter(source)
        policy = PolicyController(
            {
                Modality.STRUCTURED: ChannelProfile(
                    Modality.STRUCTURED,
                    reliability=0.995,
                    cost=0.4,
                    directness=1.0,
                )
            }
        )
        runtime = APRRuntime(
            world,
            store,
            policy,
            Budget(5.0),
            {Modality.STRUCTURED: adapter},
        )

        goal = Goal("browser.url", min_confidence=0.9)
        first, evidence = runtime.step(goal)
        self.assertEqual(evidence.observed_value, "https://a")

        second, evidence = runtime.step(goal)
        self.assertEqual(second.mode, ReadingMode.NO_OBSERVATION)
        self.assertIsNone(evidence)


if __name__ == "__main__":
    unittest.main()
