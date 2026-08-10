import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    ActionOutcomeSpec,
    ActionOutcomeVerifier,
    Evidence,
    EvidenceStore,
    Modality,
    OutcomeDecisionKind,
    PostconditionRequirement,
    WorldState,
)


def add(world, key, value, source, confidence=0.99, timestamp=None):
    ev = Evidence(
        claim_key=key,
        observed_value=value,
        modality=Modality.STRUCTURED,
        source=source,
        confidence=confidence,
        cost=0.0,
        timestamp=time.time() if timestamp is None else timestamp,
    )
    world.revise(ev)
    return ev


class OutcomeVerifierTests(unittest.TestCase):
    def setUp(self):
        self.store = EvidenceStore()
        self.world = WorldState(self.store)
        self.verifier = ActionOutcomeVerifier(self.world, self.store)

    def test_pre_action_matching_state_cannot_prove_success(self):
        t0 = time.time()
        add(self.world, "lamp.state", "on", "old_sensor", timestamp=t0 - 10)
        spec = ActionOutcomeSpec(
            "turn_on",
            (
                PostconditionRequirement(
                    "lamp.state",
                    expected_values=("on",),
                    require_post_action_evidence=True,
                ),
            ),
            verification_timeout=5,
        )
        decision = self.verifier.decide(
            spec,
            execution_id="x",
            executed_at=t0,
            pre_state={"lamp.state": "on"},
            retry_count=0,
            now=t0 + 1,
        )
        self.assertEqual(decision.kind, OutcomeDecisionKind.VERIFY)

    def test_post_action_matching_evidence_proves_success(self):
        t0 = time.time()
        add(self.world, "lamp.state", "off", "old", timestamp=t0 - 2)
        self.world.configure_fact("lamp.state", volatile=True)
        add(self.world, "lamp.state", "on", "new", timestamp=t0 + 0.1)
        spec = ActionOutcomeSpec(
            "turn_on",
            (
                PostconditionRequirement(
                    "lamp.state",
                    expected_values=("on",),
                    min_confidence=0.9,
                ),
            ),
        )
        decision = self.verifier.decide(
            spec,
            execution_id="x",
            executed_at=t0,
            pre_state={"lamp.state": "off"},
            retry_count=0,
            now=t0 + 0.2,
        )
        self.assertEqual(decision.kind, OutcomeDecisionKind.SUCCESS)

    def test_observed_false_postcondition_can_retry(self):
        t0 = time.time()
        add(self.world, "door.state", "closed", "post", timestamp=t0 + 0.1)
        spec = ActionOutcomeSpec(
            "open",
            (
                PostconditionRequirement(
                    "door.state",
                    expected_values=("open",),
                ),
            ),
            max_retries=1,
            retry_safe=True,
        )
        decision = self.verifier.decide(
            spec,
            execution_id="x",
            executed_at=t0,
            pre_state={"door.state": "closed"},
            retry_count=0,
            now=t0 + 1,
        )
        self.assertEqual(decision.kind, OutcomeDecisionKind.RETRY)

    def test_exhausted_retry_replans(self):
        t0 = time.time()
        add(self.world, "door.state", "closed", "post", timestamp=t0 + 0.1)
        spec = ActionOutcomeSpec(
            "open",
            (
                PostconditionRequirement(
                    "door.state",
                    expected_values=("open",),
                ),
            ),
            max_retries=1,
            retry_safe=True,
        )
        decision = self.verifier.decide(
            spec,
            execution_id="x",
            executed_at=t0,
            pre_state={"door.state": "closed"},
            retry_count=1,
            now=t0 + 1,
        )
        self.assertEqual(decision.kind, OutcomeDecisionKind.REPLAN)

    def test_rollback_policy_wins_on_failure(self):
        t0 = time.time()
        add(self.world, "deployment.healthy", False, "health", timestamp=t0 + 0.1)
        spec = ActionOutcomeSpec(
            "deploy",
            (
                PostconditionRequirement(
                    "deployment.healthy",
                    expected_values=(True,),
                ),
            ),
            rollback_on_failure=True,
            rollback_action_id="rollback_deploy",
        )
        decision = self.verifier.decide(
            spec,
            execution_id="x",
            executed_at=t0,
            pre_state={"deployment.healthy": True},
            retry_count=0,
            now=t0 + 1,
        )
        self.assertEqual(decision.kind, OutcomeDecisionKind.ROLLBACK)
        self.assertEqual(decision.rollback_action_id, "rollback_deploy")

    def test_timeout_turns_unverified_into_retry(self):
        t0 = time.time()
        spec = ActionOutcomeSpec(
            "press",
            (
                PostconditionRequirement(
                    "dialog.visible",
                    expected_values=(True,),
                ),
            ),
            verification_timeout=0.1,
            max_retries=1,
            retry_safe=True,
        )
        decision = self.verifier.decide(
            spec,
            execution_id="x",
            executed_at=t0,
            pre_state={"dialog.visible": None},
            retry_count=0,
            now=t0 + 1,
        )
        self.assertEqual(decision.kind, OutcomeDecisionKind.RETRY)


if __name__ == "__main__":
    unittest.main()
