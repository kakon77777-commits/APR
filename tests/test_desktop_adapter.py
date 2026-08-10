import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    APRRuntime,
    Budget,
    ChannelProfile,
    DesktopStructuredAdapter,
    EvidenceStore,
    ForegroundWindowSnapshot,
    Goal,
    Modality,
    PolicyController,
    ReadingMode,
    WorldState,
)


class FakeForeground:
    def snapshot(self):
        return ForegroundWindowSnapshot(123, "Test Window", 456)


class DesktopAdapterTests(unittest.TestCase):
    def test_runtime_can_read_real_style_structured_fact(self):
        store = EvidenceStore()
        world = WorldState(store)
        adapter = DesktopStructuredAdapter(FakeForeground())
        policy = PolicyController(
            {
                Modality.STRUCTURED: ChannelProfile(
                    Modality.STRUCTURED,
                    reliability=0.99,
                    cost=0.5,
                    directness=1.0,
                )
            }
        )
        rt = APRRuntime(
            world,
            store,
            policy,
            Budget(10),
            {Modality.STRUCTURED: adapter},
        )

        goal = Goal("desktop.foreground.title", min_confidence=0.9)
        action, evidence = rt.step(goal)
        self.assertEqual(evidence.observed_value, "Test Window")
        self.assertEqual(world.get("desktop.foreground.title").value, "Test Window")

        action, evidence = rt.step(goal)
        self.assertEqual(action.mode, ReadingMode.NO_OBSERVATION)
        self.assertIsNone(evidence)


if __name__ == "__main__":
    unittest.main()
