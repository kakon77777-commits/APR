import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    ActionDecisionKind,
    ActionGatePolicy,
    ActionReadinessGate,
    ActionSpec,
    Evidence,
    EvidenceStore,
    FactRequirement,
    FactStatus,
    Modality,
    WorldState,
)


def add(
    world,
    key,
    value,
    source,
    modality=Modality.STRUCTURED,
    confidence=0.99,
    metadata=None,
    timestamp=None,
):
    ev = Evidence(
        claim_key=key,
        observed_value=value,
        modality=modality,
        source=source,
        confidence=confidence,
        cost=0.0,
        timestamp=time.time() if timestamp is None else timestamp,
        metadata=metadata or {},
    )
    world.revise(ev)
    return ev


class ActionGateTests(unittest.TestCase):
    def setUp(self):
        self.store = EvidenceStore()
        self.world = WorldState(self.store)

    def test_unknown_fact_requires_verify(self):
        gate = ActionReadinessGate(self.world, self.store)
        action = ActionSpec(
            "a",
            "Do A",
            0.2,
            (FactRequirement("x", min_confidence=0.8),),
        )
        decision = gate.evaluate(action)
        self.assertEqual(decision.kind, ActionDecisionKind.VERIFY)
        self.assertEqual(decision.facts_to_verify, ("x",))

    def test_false_semantic_precondition_blocks(self):
        add(self.world, "door.open", False, "sensor")
        gate = ActionReadinessGate(self.world, self.store)
        action = ActionSpec(
            "cross",
            "Cross doorway",
            0.8,
            (FactRequirement("door.open", allowed_values=(True,)),),
        )
        decision = gate.evaluate(action)
        self.assertEqual(decision.kind, ActionDecisionKind.BLOCK)
        self.assertEqual(decision.blocking_facts, ("door.open",))

    def test_high_risk_action_requires_independent_evidence(self):
        add(self.world, "payee.identity", "ACME", "api")
        gate = ActionReadinessGate(
            self.world,
            self.store,
            policy=ActionGatePolicy(
                high_risk_min_independent_evidence=2,
            ),
        )
        action = ActionSpec(
            "pay",
            "Pay",
            0.9,
            (FactRequirement("payee.identity", min_confidence=0.9),),
        )
        decision = gate.evaluate(action)
        self.assertEqual(decision.kind, ActionDecisionKind.VERIFY)
        self.assertEqual(
            decision.assessments[0].evidence.independent_groups,
            1,
        )

        add(
            self.world,
            "payee.identity",
            "ACME",
            "vlm",
            modality=Modality.VISION,
        )
        decision = gate.evaluate(action)
        self.assertEqual(decision.kind, ActionDecisionKind.ALLOW)

    def test_same_asset_revisit_is_not_independent(self):
        add(
            self.world,
            "x",
            1,
            "model_a",
            modality=Modality.VISION,
            metadata={"source_asset": "/same/frame.png"},
        )
        add(
            self.world,
            "x",
            1,
            "model_b",
            modality=Modality.VISION,
            metadata={"source_asset": "/same/frame.png", "revisit_of": "old"},
        )
        gate = ActionReadinessGate(
            self.world,
            self.store,
            policy=ActionGatePolicy(
                high_risk_min_independent_evidence=2,
            ),
        )
        action = ActionSpec(
            "risky",
            "Risky",
            0.9,
            (FactRequirement("x"),),
        )
        decision = gate.evaluate(action)
        self.assertEqual(decision.kind, ActionDecisionKind.VERIFY)
        self.assertEqual(
            decision.assessments[0].evidence.independent_groups,
            1,
        )

    def test_max_age_can_be_stricter_than_fact_ttl(self):
        old = time.time() - 10
        add(self.world, "robot.pose.valid", True, "localizer", timestamp=old)
        self.world.configure_fact("robot.pose.valid", ttl=100)
        gate = ActionReadinessGate(self.world, self.store)
        action = ActionSpec(
            "move",
            "Move",
            0.6,
            (FactRequirement("robot.pose.valid", max_age=2),),
        )
        decision = gate.evaluate(action, now=time.time())
        self.assertEqual(decision.kind, ActionDecisionKind.VERIFY)
        self.assertIn("stale", decision.assessments[0].reason.lower())

    def test_contradiction_blocks_by_default(self):
        add(self.world, "door.state", "open", "sensor")
        add(
            self.world,
            "door.state",
            "closed",
            "vision",
            modality=Modality.VISION,
        )
        self.assertEqual(
            self.world.get("door.state").status,
            FactStatus.CONTRADICTED,
        )
        gate = ActionReadinessGate(self.world, self.store)
        action = ActionSpec(
            "move",
            "Move",
            0.5,
            (FactRequirement("door.state"),),
        )
        decision = gate.evaluate(action)
        self.assertEqual(decision.kind, ActionDecisionKind.BLOCK)

    def test_satisfied_action_is_allowed(self):
        add(self.world, "ready", True, "sensor")
        gate = ActionReadinessGate(
            self.world,
            self.store,
            policy=ActionGatePolicy(
                high_risk_min_independent_evidence=1,
            ),
        )
        action = ActionSpec(
            "go",
            "Go",
            0.2,
            (FactRequirement("ready", allowed_values=(True,)),),
        )
        decision = gate.evaluate(action)
        self.assertEqual(decision.kind, ActionDecisionKind.ALLOW)
        self.assertTrue(decision.ready)


if __name__ == "__main__":
    unittest.main()


class ActionGateRiskOverrideTests(unittest.TestCase):
    def test_single_authoritative_confirmation_can_opt_out_of_global_diversity_floor(
        self,
    ):
        store = EvidenceStore()
        world = WorldState(store)
        world.revise(
            Evidence(
                "user.confirmed",
                True,
                Modality.STRUCTURED,
                "user_confirmation",
                0.999,
                0.0,
            )
        )
        gate = ActionReadinessGate(
            world,
            store,
            policy=ActionGatePolicy(high_risk_min_independent_evidence=2),
        )
        action = ActionSpec(
            "pay",
            "Pay",
            0.95,
            (
                FactRequirement(
                    "user.confirmed",
                    min_confidence=0.99,
                    allowed_values=(True,),
                    min_independent_evidence=1,
                    inherit_risk_floor=False,
                ),
            ),
        )
        self.assertEqual(gate.evaluate(action).kind, ActionDecisionKind.ALLOW)
