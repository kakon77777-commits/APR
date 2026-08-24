from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "site/src/demo_export.py"
VALIDATION_PATH = ROOT / "site/src/publication_validation.py"
CONTENT_PATH = ROOT / "site/src/content.py"

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

        content_spec = importlib.util.spec_from_file_location("apr_site_demo_content", CONTENT_PATH)
        if content_spec is None or content_spec.loader is None:
            raise RuntimeError(f"Cannot load site content from {CONTENT_PATH}")
        cls.content = importlib.util.module_from_spec(content_spec)
        sys.modules[content_spec.name] = cls.content
        content_spec.loader.exec_module(cls.content)

        if not VALIDATION_PATH.is_file():
            cls.validator = None
        else:
            validation_spec = importlib.util.spec_from_file_location(
                "apr_site_publication_validation", VALIDATION_PATH
            )
            if validation_spec is None or validation_spec.loader is None:
                raise RuntimeError(f"Cannot load publication validator from {VALIDATION_PATH}")
            cls.validator = importlib.util.module_from_spec(validation_spec)
            validation_spec.loader.exec_module(cls.validator)

    def assert_invalid_matrix(self, matrix: object) -> None:
        if self.validator is None:
            self.fail("production publication validator is unavailable")
        with self.assertRaises(ValueError):
            self.validator.validate_scenarios(matrix)

    def assert_invalid_publication(
        self,
        *,
        routes: object | None = None,
        pages: object | None = None,
        evidence: object | None = None,
        lab_ui: object | None = None,
    ) -> None:
        if self.validator is None or not hasattr(self.validator, "validate_publication"):
            self.fail("whole-publication validator is unavailable")
        with self.assertRaises(ValueError):
            self.validator.validate_publication(
                scenarios=self.module.export_scenarios(),
                locales=self.content.LOCALES,
                routes=copy.deepcopy(self.content.ROUTES) if routes is None else routes,
                pages=copy.deepcopy(self.content.PAGES) if pages is None else pages,
                evidence=copy.deepcopy(self.content.EVIDENCE) if evidence is None else evidence,
                lab_ui=copy.deepcopy(self.content.LAB_UI) if lab_ui is None else lab_ui,
            )

    def test_matrix_covers_every_control_combination(self):
        matrix = self.module.export_scenarios()
        self.assertEqual(64, len(matrix))
        self.assertEqual(64, len(set(matrix)))

    def test_production_validator_accepts_the_real_export(self):
        self.assertTrue(
            VALIDATION_PATH.is_file(),
            "site builds need a dedicated production publication validator",
        )
        spec = importlib.util.spec_from_file_location(
            "apr_site_publication_validation", VALIDATION_PATH
        )
        if spec is None or spec.loader is None:
            self.fail(f"Cannot load publication validator from {VALIDATION_PATH}")
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)

        self.assertIsNone(validator.validate_scenarios(self.module.export_scenarios()))

    def test_content_owns_complete_bilingual_lab_value_maps(self):
        self.assertTrue(
            hasattr(self.content, "LAB_UI"),
            "content.py must own the complete bilingual Lab interface contract",
        )
        expected_domains = {
            "disposition": {
                "no_observation",
                "monitor",
                "skim",
                "search",
                "track",
                "inspect",
                "deep",
                "revisit",
                "epistemic_action",
            },
            "reason_key": {
                "fresh_fact_sufficient",
                "contradiction_revisit",
                "stale_fact_refresh",
                "fact_unknown_or_uncertain",
                "risk_reverification",
                "no_direct_modality",
            },
            "effective_fact_status": {
                "known",
                "unknown",
                "uncertain",
                "stale",
                "contradicted",
            },
            "selected_channel": {
                "text",
                "vision",
                "video",
                "audio",
                "structured",
                "sensor",
                "none",
            },
            "affordable": {"true", "false"},
            "action_readiness": {"allow", "verify", "block"},
        }
        self.assertEqual({"en", "zh-TW"}, set(self.content.LAB_UI))
        for locale in ("en", "zh-TW"):
            value_labels = self.content.LAB_UI[locale]["value_labels"]
            self.assertEqual(set(expected_domains), set(value_labels), locale)
            for field, expected in expected_domains.items():
                self.assertEqual(expected, set(value_labels[field]), f"{locale}:{field}")
                self.assertTrue(
                    all(
                        type(label) is str and label.strip()
                        for label in value_labels[field].values()
                    ),
                    f"{locale}:{field}",
                )

    def test_production_validator_accepts_current_locale_and_translation_contract(self):
        if self.validator is None:
            self.fail("production publication validator is unavailable")
        self.assertTrue(
            hasattr(self.validator, "validate_publication"),
            "site builds need one whole-publication validation entry point",
        )

    def test_production_validator_rejects_bilingual_route_drift(self):
        pages = copy.deepcopy(self.content.PAGES)
        pages["zh-TW"].pop("lab")
        self.assert_invalid_publication(pages=pages)

        routes = copy.deepcopy(self.content.ROUTES)
        routes[0].title.pop("zh-TW")
        self.assert_invalid_publication(routes=routes)

    def test_production_validator_rejects_bilingual_evidence_id_drift(self):
        pages = copy.deepcopy(self.content.PAGES)
        pages["zh-TW"]["lab"]["evidence_ids"] = ("lab_runtime", "action_gate")
        self.assert_invalid_publication(pages=pages)

    def test_production_validator_rejects_incomplete_value_or_reason_translation(self):
        for field, code in (
            ("disposition", "search"),
            ("reason_key", "fact_unknown_or_uncertain"),
            ("effective_fact_status", "unknown"),
            ("selected_channel", "structured"),
            ("selected_channel", "none"),
            ("affordable", "true"),
            ("action_readiness", "verify"),
        ):
            with self.subTest(field=field, code=code):
                lab_ui = copy.deepcopy(self.content.LAB_UI)
                del lab_ui["zh-TW"]["value_labels"][field][code]
                self.assert_invalid_publication(lab_ui=lab_ui)
        self.assertIsNone(
            self.validator.validate_publication(
                scenarios=self.module.export_scenarios(),
                locales=self.content.LOCALES,
                routes=self.content.ROUTES,
                pages=self.content.PAGES,
                evidence=self.content.EVIDENCE,
                lab_ui=self.content.LAB_UI,
            )
        )

    def test_production_validator_rejects_missing_or_extra_scenarios(self):
        original = self.module.export_scenarios()
        missing = copy.deepcopy(original)
        missing.pop("fresh:low:low:absent:available:unresolved")
        self.assert_invalid_matrix(missing)

        extra = copy.deepcopy(original)
        extra["fresh:low:low:absent:available:other"] = copy.deepcopy(next(iter(extra.values())))
        self.assert_invalid_matrix(extra)

    def test_production_validator_rejects_a_row_scenario_key_mismatch(self):
        matrix = copy.deepcopy(self.module.export_scenarios())
        key = "fresh:low:low:absent:available:unresolved"
        matrix[key]["scenario_key"] = "stale:high:high:present:exhausted:satisfied"
        self.assert_invalid_matrix(matrix)

    def test_production_validator_rejects_extra_or_forbidden_fields(self):
        matrix = copy.deepcopy(self.module.export_scenarios())
        first = next(iter(matrix.values()))
        first["evidence_id"] = "private-pointer"
        self.assert_invalid_matrix(matrix)

    def test_production_validator_rejects_forbidden_terms_in_recursive_content(self):
        for forbidden in (
            "request_id",
            "local_path",
            "pointer",
            "access_token",
            "credential",
            "private",
            "raw-response",
        ):
            with self.subTest(forbidden=forbidden):
                matrix = copy.deepcopy(self.module.export_scenarios())
                next(iter(matrix.values()))["facts_to_verify"] = [forbidden]
                self.assert_invalid_matrix(matrix)

    def test_production_validator_rejects_plural_composite_mapping_keys(self):
        for forbidden in (
            "credentials",
            "access_tokens",
            "raw_responses",
            "user_ids",
            "file_paths",
            "pointers",
        ):
            with self.subTest(forbidden=forbidden):
                matrix = copy.deepcopy(self.module.export_scenarios())
                next(iter(matrix.values()))["facts_to_verify"] = [{"safe": {forbidden: "public"}}]
                with self.assertRaisesRegex(ValueError, "forbidden field name"):
                    self.validator.validate_scenarios(matrix)

    def test_production_validator_rejects_plural_composite_nested_string_values(self):
        for forbidden in (
            "credentials",
            "access_tokens",
            "raw_responses",
            "user_ids",
            "file_paths",
            "pointers",
        ):
            placements = (
                ("mapping", {"safe": forbidden}),
                ("list", ["safe", forbidden]),
                ("tuple", ("safe", forbidden)),
            )
            for placement, nested in placements:
                with self.subTest(forbidden=forbidden, placement=placement):
                    matrix = copy.deepcopy(self.module.export_scenarios())
                    next(iter(matrix.values()))["facts_to_verify"] = [nested]
                    with self.assertRaisesRegex(ValueError, "forbidden serialized content"):
                        self.validator.validate_scenarios(matrix)

    def test_production_validator_does_not_use_forbidden_substring_matching(self):
        matrix = copy.deepcopy(self.module.export_scenarios())
        next(iter(matrix.values()))["facts_to_verify"] = [
            "identity",
            "pathology",
            "pointerless",
            "tokenizer",
            "credentialed",
            "privateer",
            "raw_responsiveness",
        ]
        self.assertIsNone(self.validator.validate_scenarios(matrix))

    def test_production_validator_rejects_boolean_or_non_numeric_number_fields(self):
        for field, invalid in (
            ("expected_gain", True),
            ("estimated_cost", False),
            ("budget_before", "10"),
            ("projected_budget_after", None),
        ):
            with self.subTest(field=field, invalid=invalid):
                matrix = copy.deepcopy(self.module.export_scenarios())
                next(iter(matrix.values()))[field] = invalid
                self.assert_invalid_matrix(matrix)

    def test_production_validator_rejects_non_finite_or_out_of_range_numbers(self):
        for field, invalid in (
            ("expected_gain", float("nan")),
            ("expected_gain", float("inf")),
            ("expected_gain", -0.001),
            ("expected_gain", 1.001),
            ("estimated_cost", -0.001),
            ("budget_before", -0.001),
            ("projected_budget_after", -0.001),
            ("projected_budget_after", 10.001),
        ):
            with self.subTest(field=field, invalid=invalid):
                matrix = copy.deepcopy(self.module.export_scenarios())
                row = next(iter(matrix.values()))
                row["budget_before"] = 10.0
                row[field] = invalid
                self.assert_invalid_matrix(matrix)

    def test_production_validator_rejects_values_outside_declared_domains(self):
        for field, invalid in (
            ("disposition", "execute"),
            ("reason_key", "provider_decision"),
            ("effective_fact_status", "private"),
            ("selected_channel", "provider"),
            ("action_readiness", "run"),
            ("affordable", 1),
        ):
            with self.subTest(field=field, invalid=invalid):
                matrix = copy.deepcopy(self.module.export_scenarios())
                next(iter(matrix.values()))[field] = invalid
                self.assert_invalid_matrix(matrix)

    def test_production_validator_rejects_malformed_fact_lists(self):
        for field, invalid in (
            ("facts_to_verify", ("demo.ready",)),
            ("facts_to_verify", [1]),
            ("blocking_facts", "demo.ready"),
            ("blocking_facts", [""]),
        ):
            with self.subTest(field=field, invalid=invalid):
                matrix = copy.deepcopy(self.module.export_scenarios())
                next(iter(matrix.values()))[field] = invalid
                self.assert_invalid_matrix(matrix)

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
