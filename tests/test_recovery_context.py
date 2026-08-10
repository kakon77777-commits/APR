import sys
import tempfile
import time
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
    PostconditionRequirement,
    RecoveryPolicy,
    RecoveryRunStatus,
    RetryMode,
    ReversibilityClass,
    WorldState,
)


class RecoveryContextTests(unittest.TestCase):
    def test_cooperative_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore()
            world = WorldState(store)
            world.configure_fact("ready", volatile=True)
            world.revise(
                Evidence(
                    "ready",
                    True,
                    Modality.STRUCTURED,
                    "pre",
                    0.99,
                    0.0,
                )
            )
            action = ActionSpec(
                "slow",
                "Slow",
                0.2,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            gate = ActionReadinessGate(
                world,
                store,
                policy=ActionGatePolicy(high_risk_min_independent_evidence=1),
            )
            readiness = ActionReadinessRuntime(gate)
            readiness.register(action)
            verifier = ActionOutcomeVerifier(world, store)
            ledger = ExecutionLedger(Path(tmp) / "exec.sqlite3")
            outcomes = ActionOutcomeRuntime(readiness, verifier, ledger)
            orch = ClosedLoopRecoveryOrchestrator(readiness, outcomes, ledger)

            def handler(ctx):
                time.sleep(0.02)
                ctx.checkpoint()
                return "late"

            orch.register(
                action,
                ActionOutcomeSpec(
                    "slow",
                    (PostconditionRequirement("done", expected_values=(True,)),),
                ),
                handler,
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.REVERSIBLE,
                    retry_mode=RetryMode.NEVER,
                    overall_timeout=0.001,
                ),
            )

            result = orch.run("slow")
            self.assertEqual(result.status, RecoveryRunStatus.TIMED_OUT)

    def test_cooperative_cancellation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore()
            world = WorldState(store)
            world.configure_fact("ready", volatile=True)
            world.revise(
                Evidence(
                    "ready",
                    True,
                    Modality.STRUCTURED,
                    "pre",
                    0.99,
                    0.0,
                )
            )
            action = ActionSpec(
                "cancel",
                "Cancel",
                0.2,
                (FactRequirement("ready", allowed_values=(True,), inherit_risk_floor=False),),
            )
            gate = ActionReadinessGate(
                world,
                store,
                policy=ActionGatePolicy(high_risk_min_independent_evidence=1),
            )
            readiness = ActionReadinessRuntime(gate)
            readiness.register(action)
            verifier = ActionOutcomeVerifier(world, store)
            ledger = ExecutionLedger(Path(tmp) / "exec.sqlite3")
            outcomes = ActionOutcomeRuntime(readiness, verifier, ledger)
            orch = ClosedLoopRecoveryOrchestrator(readiness, outcomes, ledger)

            def handler(ctx):
                ctx.cancel()
                ctx.checkpoint()

            orch.register(
                action,
                ActionOutcomeSpec(
                    "cancel",
                    (PostconditionRequirement("done", expected_values=(True,)),),
                ),
                handler,
                recovery=RecoveryPolicy(
                    reversibility=ReversibilityClass.REVERSIBLE,
                    retry_mode=RetryMode.NEVER,
                    overall_timeout=1.0,
                ),
            )

            result = orch.run("cancel")
            self.assertEqual(result.status, RecoveryRunStatus.CANCELLED)


if __name__ == "__main__":
    unittest.main()
