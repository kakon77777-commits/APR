import math
import unittest

from apr_runtime import (
    Budget,
    ChannelProfile,
    Evidence,
    Goal,
    Modality,
    PerceptualAction,
    ReadingMode,
)


class ModelValidationTests(unittest.TestCase):
    def test_negative_cost_cannot_credit_budget(self):
        budget = Budget(10.0)
        self.assertFalse(budget.can_afford(-1.0))
        with self.assertRaises(ValueError):
            budget.spend(-1.0)
        self.assertEqual(budget.remaining, 10.0)

    def test_budget_rejects_non_finite_values(self):
        with self.assertRaises(ValueError):
            Budget(math.inf)
        with self.assertRaises(ValueError):
            Budget(10.0, spent=11.0)

    def test_evidence_rejects_invalid_confidence_and_cost(self):
        with self.assertRaises(ValueError):
            Evidence("fact", True, Modality.SENSOR, "sensor", 1.1, 0.0)
        with self.assertRaises(ValueError):
            Evidence("fact", True, Modality.SENSOR, "sensor", 0.9, -0.1)

    def test_goal_rejects_invalid_risk(self):
        with self.assertRaises(ValueError):
            Goal("fact", risk=-0.1)

    def test_action_rejects_negative_cost(self):
        with self.assertRaises(ValueError):
            PerceptualAction(
                target="fact",
                modality=Modality.SENSOR,
                mode=ReadingMode.INSPECT,
                expected_gain=0.5,
                estimated_cost=-1.0,
                reason="invalid",
            )

    def test_channel_profile_rejects_invalid_ranges(self):
        with self.assertRaises(ValueError):
            ChannelProfile(Modality.SENSOR, reliability=1.2, cost=1.0)
        with self.assertRaises(ValueError):
            ChannelProfile(Modality.SENSOR, reliability=0.9, cost=-1.0)


if __name__ == "__main__":
    unittest.main()
