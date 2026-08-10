import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    APRRuntime,
    Budget,
    ChannelProfile,
    Evidence,
    EvidenceStore,
    FactStatus,
    Goal,
    Modality,
    ObservationSpec,
    PolicyController,
    ReadingMode,
    SimulatorAdapter,
    WorldState,
)


def build_runtime():
    store = EvidenceStore()
    world = WorldState(store)
    sensor = SimulatorAdapter(
        Modality.SENSOR,
        "sensor",
        {"door.state": ObservationSpec("open", 0.99)},
        reliability=0.99,
        base_cost=1.0,
    )
    vision = SimulatorAdapter(
        Modality.VISION,
        "vision",
        {"door.state": ObservationSpec("open", 0.97)},
        reliability=0.95,
        base_cost=5.0,
    )
    profiles = {
        Modality.SENSOR: ChannelProfile(Modality.SENSOR, 0.99, 1.0, True, 1.0),
        Modality.VISION: ChannelProfile(Modality.VISION, 0.95, 5.0, True, 0.65),
    }
    return APRRuntime(
        world,
        store,
        PolicyController(profiles),
        Budget(50.0),
        {Modality.SENSOR: sensor, Modality.VISION: vision},
    )


class APRRuntimeTests(unittest.TestCase):
    def test_fresh_state_skips_observation(self):
        rt = build_runtime()
        goal = Goal("door.state", min_confidence=0.8)
        first, _ = rt.step(goal)
        self.assertNotEqual(first.mode, ReadingMode.NO_OBSERVATION)
        spent = rt.budget.spent

        second, ev = rt.step(goal)
        self.assertEqual(second.mode, ReadingMode.NO_OBSERVATION)
        self.assertIsNone(ev)
        self.assertEqual(spent, rt.budget.spent)

    def test_stale_state_triggers_inspection(self):
        rt = build_runtime()
        goal = Goal("door.state", min_confidence=0.8)
        rt.step(goal)
        fact = rt.world.get("door.state")
        fact.ttl = 0.01
        fact.last_verified = time.time() - 1.0

        action = rt.decide(goal)
        self.assertEqual(action.mode, ReadingMode.INSPECT)

    def test_conflict_triggers_revisit(self):
        rt = build_runtime()
        goal = Goal("door.state", min_confidence=0.8)
        rt.step(goal)

        rt.world.revise(
            Evidence(
                "door.state",
                "closed",
                Modality.VISION,
                "vision",
                0.95,
                5.0,
            )
        )
        self.assertEqual(rt.world.get("door.state").status, FactStatus.CONTRADICTED)

        action = rt.decide(Goal("door.state", risk=0.9, min_confidence=0.9))
        self.assertEqual(action.mode, ReadingMode.REVISIT)

    def test_budget_is_spent_only_on_observation(self):
        rt = build_runtime()
        goal = Goal("door.state", min_confidence=0.8)
        action, _ = rt.step(goal)
        self.assertGreater(rt.budget.spent, 0)
        spent = rt.budget.spent

        action, _ = rt.step(goal)
        self.assertEqual(action.mode, ReadingMode.NO_OBSERVATION)
        self.assertEqual(rt.budget.spent, spent)

    def test_provenance_is_preserved(self):
        rt = build_runtime()
        rt.step(Goal("door.state", min_confidence=0.8))
        fact = rt.world.get("door.state")
        self.assertEqual(len(fact.evidence_ids), 1)
        self.assertIsNotNone(rt.evidence_store.get(fact.evidence_ids[0]))


if __name__ == "__main__":
    unittest.main()
