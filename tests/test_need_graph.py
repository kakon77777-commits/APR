import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    Evidence,
    EvidenceStore,
    Modality,
    NeedState,
    PerceptualNeed,
    PerceptualNeedGraph,
    WorldState,
)


class NeedGraphTests(unittest.TestCase):
    def setUp(self):
        self.store = EvidenceStore()
        self.world = WorldState(self.store)
        self.graph = PerceptualNeedGraph()

    def test_unknown_need_is_urgent(self):
        self.graph.add_need(PerceptualNeed("n1", "door.state", risk=0.8))
        a = self.graph.assess("n1", self.world)
        self.assertEqual(a.state, NeedState.UNKNOWN)
        self.assertGreater(a.urgency, 0.7)

    def test_known_fact_satisfies_need_and_graph_ready(self):
        self.graph.add_need(PerceptualNeed("n1", "door.state", min_confidence=0.8))
        self.world.revise(Evidence("door.state", "open", Modality.SENSOR, "s", 0.95, 0.1))
        a = self.graph.assess("n1", self.world)
        self.assertEqual(a.state, NeedState.SATISFIED)
        self.assertEqual(a.urgency, 0.0)
        self.assertTrue(self.graph.ready(self.world))

    def test_dependency_blocks_parent_until_prerequisite_satisfied(self):
        self.graph.add_need(PerceptualNeed("identity", "bottle.identity"))
        self.graph.add_need(PerceptualNeed("safe", "bottle.safe"))
        self.graph.add_dependency("safe", "identity")
        self.world.revise(Evidence("bottle.safe", True, Modality.VISION, "v", 0.95, 1.0))
        self.assertEqual(
            self.graph.assess("safe", self.world).state,
            NeedState.BLOCKED,
        )
        self.world.revise(Evidence("bottle.identity", "A", Modality.VISION, "v", 0.95, 1.0))
        self.assertEqual(
            self.graph.assess("safe", self.world).state,
            NeedState.SATISFIED,
        )

    def test_stale_fact_reenters_frontier(self):
        self.graph.add_need(PerceptualNeed("n1", "person.position"))
        self.world.configure_fact("person.position", ttl=0.01, volatile=True)
        self.world.revise(
            Evidence(
                "person.position",
                "left",
                Modality.VISION,
                "v",
                0.95,
                1.0,
                timestamp=time.time() - 1,
            )
        )
        a = self.graph.assess("n1", self.world)
        self.assertEqual(a.state, NeedState.STALE)
        self.assertEqual(
            self.graph.frontier(self.world)[0].fact_key,
            "person.position",
        )


if __name__ == "__main__":
    unittest.main()
