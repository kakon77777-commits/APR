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
    ClosedLoopRecoveryOrchestrator,
    Evidence,
    EvidenceStore,
    ExecutionLedger,
    FactRequirement,
    Modality,
    PartialSuccessPolicy,
    PostconditionRequirement,
    RecoveryPolicy,
    RecoveryRunStatus,
    RetryMode,
    ReversibilityClass,
    WorldState,
)


def add(world, key, value, source, confidence=0.99):
    ev = Evidence(
        claim_key=key,
        observed_value=value,
        modality=Modality.STRUCTURED,
        source=source,
        confidence=confidence,
        cost=0.0,
    )
    world.revise(ev)
    return ev


def base(tmp):
    store = EvidenceStore()
    world = WorldState(store)
    world.configure_fact("ready", volatile=True)
    add(world, "ready", True, "pre")

    gate = ActionReadinessGate(
        world,
        store,
        policy=ActionGatePolicy(
            high_risk_min_independent_evidence=1,
        ),
    )
    readiness = ActionReadinessRuntime(gate)
    verifier = ActionOutcomeVerifier(world, store)
    ledger = ExecutionLedger(Path(tmp) / "exec.sqlite3")
    outcomes = ActionOutcomeRuntime(readiness, verifier, ledger)
    orchestrator = ClosedLoopRecoveryOrchestrator(readiness, outcomes, ledger)
    return store, world, readiness, outcomes, ledger, orchestrator


class RecoveryOrchestratorTests(unittest.TestCase):
    def test_retry_lineage_and_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, world, readiness, _, ledger, orch = base(tmp)
            action = ActionSpec(
                "do",
                "Do",
                0.2,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            attempt = {"n": 0}

            def handler(ctx):
                attempt["n"] += 1
                return attempt["n"]

            def observer(execution_id, ctx):
                world.configure_fact("done", volatile=True)
                add(
                    world,
                    "done",
                    attempt["n"] >= 2,
                    f"post_{attempt['n']}",
                )

            orch.register(
                action,
                ActionOutcomeSpec(
                    "do",
                    (PostconditionRequirement("done", expected_values=(True,)),),
                    max_retries=1,
                    retry_safe=True,
                ),
                handler,
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.COMPENSATABLE,
                    retry_mode=RetryMode.IDEMPOTENT,
                    max_attempts=2,
                ),
                observer=observer,
            )

            result = orch.run("do")
            self.assertEqual(result.status, RecoveryRunStatus.SUCCESS)
            receipts = ledger.recent(action_id="do", limit=10)
            self.assertEqual(len(receipts), 2)
            by_retry = sorted(receipts, key=lambda r: r.retry_count)
            self.assertIsNone(by_retry[0].parent_execution_id)
            self.assertEqual(
                by_retry[1].parent_execution_id,
                by_retry[0].id,
            )

    def test_irreversible_action_does_not_auto_retry_without_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, world, _, _, ledger, orch = base(tmp)
            action = ActionSpec(
                "send",
                "Send",
                0.9,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )

            def observer(execution_id, ctx):
                world.configure_fact("sent", volatile=True)
                add(world, "sent", False, "post")

            orch.register(
                action,
                ActionOutcomeSpec(
                    "send",
                    (PostconditionRequirement("sent", expected_values=(True,)),),
                    max_retries=5,
                    retry_safe=True,
                ),
                lambda ctx: "sent?",
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.IRREVERSIBLE,
                    retry_mode=RetryMode.IDEMPOTENT,
                    max_attempts=5,
                ),
                observer=observer,
            )

            result = orch.run("send")
            self.assertEqual(
                result.status,
                RecoveryRunStatus.REPLAN_REQUIRED,
            )
            self.assertEqual(len(ledger.recent(action_id="send")), 1)

    def test_irreversible_deduplicated_retry_requires_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, world, _, _, ledger, orch = base(tmp)
            action = ActionSpec(
                "charge",
                "Charge",
                0.9,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            attempts = {"n": 0}

            def handler(ctx):
                attempts["n"] += 1
                return attempts["n"]

            def observer(execution_id, ctx):
                world.configure_fact("charged", volatile=True)
                add(
                    world,
                    "charged",
                    attempts["n"] >= 2,
                    f"post_{attempts['n']}",
                )

            orch.register(
                action,
                ActionOutcomeSpec(
                    "charge",
                    (PostconditionRequirement("charged", expected_values=(True,)),),
                    max_retries=1,
                    retry_safe=True,
                ),
                handler,
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.IRREVERSIBLE,
                    retry_mode=RetryMode.DEDUPLICATED,
                    max_attempts=2,
                ),
                observer=observer,
            )

            denied = orch.run("charge")
            self.assertEqual(
                denied.status,
                RecoveryRunStatus.REPLAN_REQUIRED,
            )

            # Fresh environment would normally be used in production; update
            # state so a second independent run can demonstrate keyed retry.
            world.configure_fact("charged", volatile=True)
            result = orch.run("charge", idempotency_key="charge-123")
            self.assertEqual(result.status, RecoveryRunStatus.SUCCESS)

    def test_compensating_action_is_gated_and_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, world, readiness, _, ledger, orch = base(tmp)

            world.configure_fact("resource.state", volatile=True)
            add(world, "resource.state", "original", "pre")

            forward = ActionSpec(
                "change",
                "Change",
                0.4,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            rollback = ActionSpec(
                "undo",
                "Undo",
                0.4,
                (
                    FactRequirement(
                        "rollback.allowed",
                        allowed_values=(True,),
                        inherit_risk_floor=False,
                    ),
                ),
            )
            world.configure_fact("rollback.allowed", volatile=True)
            add(world, "rollback.allowed", True, "policy")

            def forward_observer(execution_id, ctx):
                add(world, "resource.state", "bad", "forward_post")

            def rollback_observer(execution_id, ctx):
                add(world, "resource.state", "original", "rollback_post")

            orch.register(
                forward,
                ActionOutcomeSpec(
                    "change",
                    (
                        PostconditionRequirement(
                            "resource.state",
                            expected_values=("good",),
                        ),
                    ),
                    rollback_on_failure=True,
                    rollback_action_id="undo",
                ),
                lambda ctx: "changed",
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.COMPENSATABLE,
                    retry_mode=RetryMode.NEVER,
                    rollback_action_id="undo",
                ),
                observer=forward_observer,
            )
            orch.register(
                rollback,
                ActionOutcomeSpec(
                    "undo",
                    (
                        PostconditionRequirement(
                            "resource.state",
                            expected_values=("original",),
                        ),
                    ),
                ),
                lambda ctx: "undone",
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.REVERSIBLE,
                    retry_mode=RetryMode.NEVER,
                ),
                observer=rollback_observer,
            )

            result = orch.run("change")
            self.assertEqual(result.status, RecoveryRunStatus.ROLLED_BACK)
            self.assertIsNotNone(result.rollback_execution_id)
            self.assertEqual(world.get("resource.state").value, "original")
            rollback_receipt = ledger.get(result.rollback_execution_id)
            self.assertEqual(rollback_receipt.status, "completed")

    def test_blocked_rollback_fails_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, world, _, _, _, orch = base(tmp)
            forward = ActionSpec(
                "change",
                "Change",
                0.4,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            rollback = ActionSpec(
                "undo",
                "Undo",
                0.4,
                (
                    FactRequirement(
                        "rollback.allowed",
                        allowed_values=(True,),
                        inherit_risk_floor=False,
                    ),
                ),
            )
            world.configure_fact("rollback.allowed", volatile=True)
            add(world, "rollback.allowed", False, "policy")
            world.configure_fact("state", volatile=True)
            add(world, "state", "old", "pre")

            orch.register(
                forward,
                ActionOutcomeSpec(
                    "change",
                    (PostconditionRequirement("state", expected_values=("new",)),),
                    rollback_on_failure=True,
                    rollback_action_id="undo",
                ),
                lambda ctx: None,
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.COMPENSATABLE,
                    rollback_action_id="undo",
                ),
                observer=lambda eid, ctx: add(world, "state", "bad", "post"),
            )
            orch.register(
                rollback,
                ActionOutcomeSpec(
                    "undo",
                    (PostconditionRequirement("state", expected_values=("old",)),),
                ),
                lambda ctx: None,
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.REVERSIBLE,
                ),
                observer=lambda eid, ctx: add(world, "state", "old", "rollback"),
            )

            result = orch.run("change")
            self.assertEqual(
                result.status,
                RecoveryRunStatus.ROLLBACK_FAILED,
            )

    def test_irreversible_deduplicated_retry_succeeds_with_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, world, _, _, ledger, orch = base(tmp)
            action = ActionSpec(
                "charge2",
                "Charge2",
                0.9,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            attempts = {"n": 0}

            def handler(ctx):
                attempts["n"] += 1
                self.assertEqual(ctx.idempotency_key, "charge-key")
                return attempts["n"]

            def observer(execution_id, ctx):
                world.configure_fact("charged2", volatile=True)
                add(
                    world,
                    "charged2",
                    attempts["n"] >= 2,
                    f"post_{attempts['n']}",
                )

            orch.register(
                action,
                ActionOutcomeSpec(
                    "charge2",
                    (PostconditionRequirement("charged2", expected_values=(True,)),),
                    max_retries=1,
                    retry_safe=True,
                ),
                handler,
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.IRREVERSIBLE,
                    retry_mode=RetryMode.DEDUPLICATED,
                    max_attempts=2,
                ),
                observer=observer,
            )

            result = orch.run(
                "charge2",
                idempotency_key="charge-key",
            )
            self.assertEqual(result.status, RecoveryRunStatus.SUCCESS)
            self.assertEqual(attempts["n"], 2)
            receipts = ledger.recent(action_id="charge2")
            self.assertEqual(len(receipts), 2)

    def test_partial_success_policy_accepts_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, world, _, _, _, orch = base(tmp)
            action = ActionSpec(
                "multi",
                "Multi",
                0.2,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )

            def observer(execution_id, ctx):
                world.configure_fact("step.a", volatile=True)
                world.configure_fact("step.b", volatile=True)
                add(world, "step.a", True, "post_a")
                add(world, "step.b", False, "post_b")

            orch.register(
                action,
                ActionOutcomeSpec(
                    "multi",
                    (
                        PostconditionRequirement("step.a", expected_values=(True,)),
                        PostconditionRequirement("step.b", expected_values=(True,)),
                    ),
                    retry_safe=False,
                ),
                lambda ctx: "partial",
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.COMPENSATABLE,
                    retry_mode=RetryMode.NEVER,
                    partial_success=PartialSuccessPolicy.ACCEPT,
                ),
                observer=observer,
            )

            result = orch.run("multi")
            self.assertEqual(
                result.status,
                RecoveryRunStatus.PARTIAL_ACCEPTED,
            )

    def test_compensation_can_retry_under_its_own_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, world, _, _, ledger, orch = base(tmp)
            world.configure_fact("state2", volatile=True)
            add(world, "state2", "old", "pre")
            world.configure_fact("rollback.ok", volatile=True)
            add(world, "rollback.ok", True, "policy")

            forward = ActionSpec(
                "forward2",
                "Forward2",
                0.3,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            rollback = ActionSpec(
                "undo2",
                "Undo2",
                0.3,
                (FactRequirement("rollback.ok", allowed_values=(True,), inherit_risk_floor=False),),
            )
            rb_attempt = {"n": 0}

            orch.register(
                forward,
                ActionOutcomeSpec(
                    "forward2",
                    (PostconditionRequirement("state2", expected_values=("good",)),),
                    rollback_on_failure=True,
                    rollback_action_id="undo2",
                ),
                lambda ctx: "forward",
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.COMPENSATABLE,
                    rollback_action_id="undo2",
                ),
                observer=lambda eid, ctx: add(world, "state2", "bad", "forward_post"),
            )

            def rollback_handler(ctx):
                rb_attempt["n"] += 1
                return rb_attempt["n"]

            def rollback_observer(eid, ctx):
                value = "bad" if rb_attempt["n"] == 1 else "old"
                add(world, "state2", value, f"rollback_post_{rb_attempt['n']}")

            orch.register(
                rollback,
                ActionOutcomeSpec(
                    "undo2",
                    (PostconditionRequirement("state2", expected_values=("old",)),),
                    max_retries=1,
                    retry_safe=True,
                ),
                rollback_handler,
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.REVERSIBLE,
                    retry_mode=RetryMode.IDEMPOTENT,
                    max_attempts=2,
                ),
                observer=rollback_observer,
            )

            result = orch.run("forward2")
            self.assertEqual(result.status, RecoveryRunStatus.ROLLED_BACK)
            self.assertEqual(rb_attempt["n"], 2)
            self.assertEqual(len(ledger.recent(action_id="undo2")), 2)

    def test_trace_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, world, _, _, _, orch = base(tmp)
            action = ActionSpec(
                "do",
                "Do",
                0.2,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            orch.register(
                action,
                ActionOutcomeSpec(
                    "do",
                    (PostconditionRequirement("done", expected_values=(True,)),),
                ),
                lambda ctx: "ok",
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.REVERSIBLE,
                ),
                observer=lambda eid, ctx: (
                    world.configure_fact("done", volatile=True),
                    add(world, "done", True, "post"),
                ),
            )
            result = orch.run("do")
            jp = result.trace.export_json(Path(tmp) / "trace.json")
            mp = result.trace.export_markdown(Path(tmp) / "trace.md")
            self.assertTrue(jp.exists())
            self.assertTrue(mp.exists())
            self.assertIn("verify_outcome", mp.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
