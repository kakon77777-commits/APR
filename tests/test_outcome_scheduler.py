import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    ActionGatePolicy,
    ActionOutcomeRuntime,
    ActionOutcomeSpec,
    ActionOutcomeVerifier,
    ActionReadinessGate,
    ActionReadinessRuntime,
    ActionSpec,
    EventFactDependencyMap,
    EventLedger,
    Evidence,
    EvidenceStore,
    ExecutionLedger,
    FactRequirement,
    Modality,
    PerceptualNeedGraph,
    PostconditionRequirement,
    SchedulerConfig,
    TaskAwareEventRouter,
    TaskAwarePerceptionRuntime,
    UnifiedEventRuntime,
    UnifiedEventScheduler,
    WorldState,
)


class OutcomeSchedulerIntegrationTests(unittest.TestCase):
    def test_execution_schedules_targeted_postcondition_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore()
            world = WorldState(store)
            world.configure_fact("ready", volatile=True)
            world.revise(Evidence("ready", True, Modality.STRUCTURED, "sensor", 0.99, 0.0))

            action = ActionSpec(
                "do",
                "Do",
                0.7,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            gate = ActionReadinessGate(
                world,
                store,
                policy=ActionGatePolicy(high_risk_min_independent_evidence=1),
            )
            needs = PerceptualNeedGraph()
            readiness = ActionReadinessRuntime(gate, needs=needs)
            readiness.register(action)

            event_ledger = EventLedger(Path(tmp) / "events.sqlite3")
            scheduler = UnifiedEventScheduler(
                config=SchedulerConfig(max_queue=20),
                ledger=event_ledger,
            )
            router = TaskAwareEventRouter(world, needs, EventFactDependencyMap())
            perception = TaskAwarePerceptionRuntime(UnifiedEventRuntime(scheduler), router)

            runtime = ActionOutcomeRuntime(
                readiness,
                ActionOutcomeVerifier(world, store),
                ExecutionLedger(Path(tmp) / "exec.sqlite3"),
                perception_runtime=perception,
            )
            runtime.register_outcome(
                ActionOutcomeSpec(
                    "do",
                    (
                        PostconditionRequirement(
                            "done", expected_values=(True,), min_confidence=0.9
                        ),
                    ),
                )
            )

            result = runtime.execute("do", lambda: "effect")
            self.assertTrue(result.executed)
            self.assertEqual(event_ledger.count(), 1)

            batch = scheduler.pop_batch(max_items=10)
            self.assertEqual(len(batch), 1)
            event = batch[0].event
            self.assertEqual(event.kind, "apr.action.outcome.verify")
            self.assertEqual(event.target, "done")
            self.assertEqual(event.payload["execution_id"], result.execution_id)
            self.assertEqual(event.payload["affected_facts"], {"done": 1.0})


if __name__ == "__main__":
    unittest.main()
