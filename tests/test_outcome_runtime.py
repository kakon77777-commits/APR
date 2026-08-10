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
    Evidence,
    EvidenceStore,
    ExecutionLedger,
    FactRequirement,
    Modality,
    OutcomeDecisionKind,
    PostconditionRequirement,
    WorldState,
)


def add(world, key, value, source, timestamp=None):
    ev = Evidence(
        claim_key=key,
        observed_value=value,
        modality=Modality.STRUCTURED,
        source=source,
        confidence=0.99,
        cost=0.0,
        timestamp=time.time() if timestamp is None else timestamp,
    )
    world.revise(ev)
    return ev


class OutcomeRuntimeTests(unittest.TestCase):
    def _runtime(self, tmp):
        store = EvidenceStore()
        world = WorldState(store)
        world.configure_fact("ready", volatile=True)
        add(world, "ready", True, "pre")

        action = ActionSpec(
            "do",
            "Do",
            0.2,
            (
                FactRequirement(
                    "ready",
                    allowed_values=(True,),
                    inherit_risk_floor=False,
                ),
            ),
        )
        gate = ActionReadinessGate(
            world,
            store,
            policy=ActionGatePolicy(
                high_risk_min_independent_evidence=1,
            ),
        )
        readiness = ActionReadinessRuntime(gate)
        readiness.register(action)

        verifier = ActionOutcomeVerifier(world, store)
        ledger = ExecutionLedger(Path(tmp) / "exec.sqlite3")
        runtime = ActionOutcomeRuntime(readiness, verifier, ledger)
        runtime.register_outcome(
            ActionOutcomeSpec(
                "do",
                (
                    PostconditionRequirement(
                        "done",
                        expected_values=(True,),
                    ),
                ),
            )
        )
        return runtime, world, ledger

    def test_execute_creates_receipt_without_inventing_postcondition(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, world, ledger = self._runtime(tmp)
            result = runtime.execute(
                "do",
                lambda: "effect",
                auto_request_verification=False,
            )
            self.assertTrue(result.executed)
            receipt = ledger.get(result.execution_id)
            self.assertEqual(receipt.status, "executed")
            self.assertIsNone(world.get("done").value)

    def test_verify_links_post_action_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, world, ledger = self._runtime(tmp)
            result = runtime.execute(
                "do",
                lambda: "effect",
                auto_request_verification=False,
            )
            time.sleep(0.001)
            ev = add(world, "done", True, "post")

            decision = runtime.verify(
                result.execution_id,
                auto_request_more_evidence=False,
            )
            self.assertEqual(decision.kind, OutcomeDecisionKind.SUCCESS)
            receipt = ledger.get(result.execution_id)
            self.assertEqual(receipt.status, "completed")
            links = ledger.evidence_links(result.execution_id)
            self.assertTrue(any(x["evidence_id"] == ev.id for x in links))


if __name__ == "__main__":
    unittest.main()
