import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    ActionDecisionKind,
    ActionGatePolicy,
    ActionReadinessGate,
    ActionReadinessRuntime,
    ActionSpec,
    EventFactDependencyMap,
    EventLedger,
    Evidence,
    EvidenceStore,
    FactRequirement,
    Modality,
    PerceptualNeedGraph,
    SchedulerConfig,
    TaskAwareEventRouter,
    TaskAwarePerceptionRuntime,
    UnifiedEventRuntime,
    UnifiedEventScheduler,
    WorldState,
)


class ActionRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.store = EvidenceStore()
        self.world = WorldState(self.store)
        self.needs = PerceptualNeedGraph()

    def _make_runtime(self, tmp):
        ledger = EventLedger(Path(tmp) / "events.sqlite3")
        scheduler = UnifiedEventScheduler(
            config=SchedulerConfig(max_queue=20),
            ledger=ledger,
        )
        deps = EventFactDependencyMap()
        router = TaskAwareEventRouter(
            self.world,
            self.needs,
            deps,
        )
        task = TaskAwarePerceptionRuntime(
            UnifiedEventRuntime(scheduler),
            router,
        )
        gate = ActionReadinessGate(
            self.world,
            self.store,
            policy=ActionGatePolicy(
                high_risk_min_independent_evidence=1,
            ),
        )
        return (
            ActionReadinessRuntime(
                gate,
                needs=self.needs,
                perception_runtime=task,
            ),
            scheduler,
            ledger,
        )

    def test_register_action_adds_perceptual_needs(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _, _ = self._make_runtime(tmp)
            action = ActionSpec(
                "click",
                "Click",
                0.4,
                (
                    FactRequirement("button.visible", min_confidence=0.9),
                    FactRequirement("button.enabled", min_confidence=0.9),
                ),
            )
            runtime.register(action)
            self.assertIn(
                "action::click::button.visible",
                self.needs.needs,
            )
            self.assertIn(
                "action::click::button.enabled",
                self.needs.needs,
            )

    def test_verify_decision_emits_scheduler_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, scheduler, ledger = self._make_runtime(tmp)
            action = ActionSpec(
                "click",
                "Click",
                0.7,
                (FactRequirement("button.visible"),),
            )
            runtime.register(action)

            report = runtime.request_verification("click")
            self.assertEqual(report.accepted, 1)
            self.assertEqual(ledger.count(), 1)

            batch = scheduler.pop_batch(max_items=5)
            self.assertEqual(len(batch), 1)
            self.assertEqual(
                batch[0].event.kind,
                "apr.action.verify",
            )
            self.assertEqual(
                batch[0].event.payload["fact_key"],
                "button.visible",
            )

    def test_guarded_executor_never_calls_function_on_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _, _ = self._make_runtime(tmp)
            action = ActionSpec(
                "delete",
                "Delete",
                0.8,
                (
                    FactRequirement(
                        "deletion.confirmed",
                        allowed_values=(True,),
                    ),
                ),
            )
            runtime.register(action)

            ev = Evidence(
                "deletion.confirmed",
                False,
                Modality.STRUCTURED,
                "user",
                0.99,
                0.0,
            )
            self.world.revise(ev)

            called = {"value": False}

            def dangerous():
                called["value"] = True
                return "deleted"

            result = runtime.execute("delete", dangerous)
            self.assertFalse(result.executed)
            self.assertFalse(called["value"])
            self.assertEqual(
                result.decision.kind,
                ActionDecisionKind.BLOCK,
            )

    def test_guarded_executor_runs_only_after_allow(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _, _ = self._make_runtime(tmp)
            action = ActionSpec(
                "open",
                "Open",
                0.2,
                (
                    FactRequirement(
                        "door.unlocked",
                        allowed_values=(True,),
                    ),
                ),
            )
            runtime.register(action)

            self.world.revise(
                Evidence(
                    "door.unlocked",
                    True,
                    Modality.SENSOR,
                    "lock_sensor",
                    0.99,
                    0.0,
                )
            )

            result = runtime.execute(
                "open",
                lambda: "opened",
            )
            self.assertTrue(result.executed)
            self.assertEqual(result.result, "opened")
            self.assertEqual(
                result.decision.kind,
                ActionDecisionKind.ALLOW,
            )


if __name__ == "__main__":
    unittest.main()


class ActionVerificationUrgencyTests(unittest.TestCase):
    def test_under_evidenced_known_fact_keeps_explicit_verification_urgency(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore()
            world = WorldState(store)
            needs = PerceptualNeedGraph()
            ledger = EventLedger(Path(tmp) / "events.sqlite3")
            scheduler = UnifiedEventScheduler(
                config=SchedulerConfig(max_queue=20),
                ledger=ledger,
            )
            router = TaskAwareEventRouter(
                world,
                needs,
                EventFactDependencyMap(),
            )
            task = TaskAwarePerceptionRuntime(
                UnifiedEventRuntime(scheduler),
                router,
            )
            gate = ActionReadinessGate(
                world,
                store,
                policy=ActionGatePolicy(high_risk_min_independent_evidence=2),
            )
            runtime = ActionReadinessRuntime(
                gate,
                needs=needs,
                perception_runtime=task,
            )
            action = ActionSpec(
                "pay",
                "Pay",
                0.9,
                (FactRequirement("invoice.total", min_confidence=0.9),),
            )
            runtime.register(action)
            world.revise(
                Evidence(
                    "invoice.total",
                    1250,
                    Modality.STRUCTURED,
                    "invoice_api",
                    0.99,
                    0.0,
                )
            )

            decision = runtime.decision("pay")
            self.assertEqual(decision.kind, ActionDecisionKind.VERIFY)
            raw = runtime.verification_events("pay", decision)[0]
            raw_sig = raw.significance
            report = runtime.request_verification("pay")
            self.assertEqual(report.accepted, 1)
            batch = scheduler.pop_batch(max_items=1)
            self.assertEqual(len(batch), 1)
            # The known fact may look "satisfied" to the generic NeedGraph,
            # but the action-specific evidence deficit is an explicit need.
            self.assertGreaterEqual(batch[0].event.significance, raw_sig)
