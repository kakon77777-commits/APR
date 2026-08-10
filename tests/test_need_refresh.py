import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    Evidence,
    EvidenceStore,
    Modality,
    NeedRefreshPlanner,
    PerceptualNeed,
    PerceptualNeedGraph,
    WorldState,
)


class NeedRefreshTests(unittest.TestCase):
    def test_only_unsatisfied_needs_emit_refresh(self):
        world = WorldState(EvidenceStore())
        graph = PerceptualNeedGraph()
        graph.add_need(PerceptualNeed("a", "a.fact", risk=0.9))
        graph.add_need(PerceptualNeed("b", "b.fact", risk=0.1))
        world.revise(Evidence("b.fact", 1, Modality.SENSOR, "s", 0.99, 0.1))
        events = NeedRefreshPlanner(world, graph).emit(now=10.0)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].target, "a.fact")
        self.assertGreaterEqual(events[0].significance, 0.85)


if __name__ == "__main__":
    unittest.main()
