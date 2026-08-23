from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "site/src/demo_export.py"

PUBLIC_ROW_FIELDS = {
    "scenario_key",
    "disposition",
    "reason_key",
    "effective_fact_status",
    "selected_channel",
    "expected_gain",
    "estimated_cost",
    "budget_before",
    "projected_budget_after",
    "affordable",
    "action_readiness",
    "facts_to_verify",
    "blocking_facts",
}


class SiteDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("apr_site_demo_export", MODULE_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load site demo exporter from {MODULE_PATH}")
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    def test_matrix_covers_every_control_combination(self):
        matrix = self.module.export_scenarios()
        self.assertEqual(64, len(matrix))
        self.assertEqual(64, len(set(matrix)))

    def test_input_key_preserves_public_control_order(self):
        scenario = self.module.DemoScenarioInput(
            freshness="stale",
            uncertainty="high",
            risk="low",
            conflict="present",
            budget="exhausted",
            goal="unresolved",
        )
        self.assertEqual(
            "stale:high:low:present:exhausted:unresolved",
            scenario.key(),
        )

    def test_known_fresh_low_risk_fact_skips_observation(self):
        row = self.module.evaluate_scenario(
            self.module.DemoScenarioInput(
                freshness="fresh",
                uncertainty="low",
                risk="low",
                conflict="absent",
                budget="available",
                goal="satisfied",
            )
        )
        self.assertEqual("no_observation", row["disposition"])
        self.assertEqual("known", row["effective_fact_status"])
        self.assertEqual("allow", row["action_readiness"])

    def test_conflict_blocks_action_and_requests_revisit(self):
        row = self.module.evaluate_scenario(
            self.module.DemoScenarioInput(
                freshness="fresh",
                uncertainty="low",
                risk="high",
                conflict="present",
                budget="available",
                goal="satisfied",
            )
        )
        self.assertEqual("revisit", row["disposition"])
        self.assertEqual("contradicted", row["effective_fact_status"])
        self.assertEqual("block", row["action_readiness"])

    def test_unresolved_goal_without_conflict_remains_unknown_even_when_stale(self):
        row = self.module.evaluate_scenario(
            self.module.DemoScenarioInput(
                freshness="stale",
                uncertainty="high",
                risk="low",
                conflict="absent",
                budget="available",
                goal="unresolved",
            )
        )
        self.assertEqual("unknown", row["effective_fact_status"])

    def test_every_exported_row_has_only_the_public_fields(self):
        for key, row in self.module.export_scenarios().items():
            self.assertEqual(PUBLIC_ROW_FIELDS, set(row), key)
            self.assertEqual(key, row["scenario_key"])

    def test_export_has_no_sensitive_or_unbounded_fields(self):
        encoded = json.dumps(self.module.export_scenarios(), sort_keys=True)
        for forbidden in (
            "pointer",
            "path",
            "token",
            "credential",
            "raw_response",
            "evidence_id",
        ):
            self.assertNotIn(forbidden, encoded.lower())

    def test_build_emits_compact_versioned_scenario_payload(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            subprocess.run(
                [sys.executable, "-B", "site/build.py", "--output", str(output)],
                cwd=ROOT,
                check=True,
            )
            payload_path = output / "data/demo-scenarios.json"
            encoded = payload_path.read_text(encoding="utf-8")
            payload = json.loads(encoded)

            self.assertEqual("apr-demo-scenarios/v1", payload["schema"])
            self.assertEqual("0.10.0", payload["runtime_version"])
            self.assertEqual(
                ["freshness", "uncertainty", "risk", "conflict", "budget", "goal"],
                payload["controls"],
            )
            self.assertEqual(64, len(payload["scenarios"]))
            self.assertEqual(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoded,
            )


if __name__ == "__main__":
    unittest.main()
