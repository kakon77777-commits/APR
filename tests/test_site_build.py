from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = ROOT / "site/src/content.py"


def load_content():
    spec = importlib.util.spec_from_file_location("apr_site_content", CONTENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load site content from {CONTENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SiteBuildTests(unittest.TestCase):
    def build(self, output: Path) -> None:
        subprocess.run(
            [sys.executable, "-B", "site/build.py", "--output", str(output)],
            cwd=ROOT,
            check=True,
        )

    def test_build_emits_every_bilingual_route(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            routes = ("", "runtime", "lab", "papers", "mcp", "status")
            for route in routes:
                english = output / route / "index.html" if route else output / "index.html"
                chinese = output / "zh-TW" / route / "index.html"
                self.assertTrue(english.is_file(), english)
                self.assertTrue(chinese.is_file(), chinese)

    def test_build_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as left_raw, tempfile.TemporaryDirectory() as right_raw:
            left, right = Path(left_raw), Path(right_raw)
            self.build(left)
            self.build(right)
            left_files = {
                p.relative_to(left): p.read_bytes() for p in left.rglob("*") if p.is_file()
            }
            right_files = {
                p.relative_to(right): p.read_bytes() for p in right.rglob("*") if p.is_file()
            }
            self.assertEqual(left_files, right_files)

    def test_machine_index_is_valid_json(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            data = json.loads((output / "ai/site.json").read_text(encoding="utf-8"))
            self.assertEqual("apr-site-index/v1", data["schema"])

    def test_locales_share_route_and_evidence_identifiers(self):
        content = load_content()
        self.assertEqual(set(content.PAGES["en"]), set(content.PAGES["zh-TW"]))
        self.assertEqual({route.slug for route in content.ROUTES}, set(content.PAGES["en"]))
        for slug in content.PAGES["en"]:
            self.assertEqual(
                content.PAGES["en"][slug]["evidence_ids"],
                content.PAGES["zh-TW"][slug]["evidence_ids"],
            )

        expected_papers = {
            "apr_01",
            "apr_02",
            "apr_03",
            "apr_04",
            "apr_05",
            "apr_06",
            "apr_07",
            "whitepaper",
            "acr_specification",
            "acr_engineering",
            "acr_moderate_cognition",
        }
        self.assertEqual(expected_papers, set(content.PAGES["en"]["papers"]["evidence_ids"]))

    def test_pages_render_immutable_evidence_links(self):
        content = load_content()
        prefix = f"https://github.com/kakon77777-commits/APR/blob/{content.SITE['source_ref']}/"
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            for slug, page in content.PAGES["en"].items():
                rendered_path = output / slug / "index.html" if slug else output / "index.html"
                rendered = rendered_path.read_text(encoding="utf-8")
                for evidence_id in page["evidence_ids"]:
                    self.assertIn(prefix + content.EVIDENCE[evidence_id], rendered)
                    self.assertIn(content.EVIDENCE[evidence_id], rendered)

    def test_evidence_paths_exist_at_candidate_source_ref(self):
        content = load_content()
        for evidence_id, path in content.EVIDENCE.items():
            result = subprocess.run(
                ["git", "cat-file", "-e", f"{content.SITE['source_ref']}:{path}"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, f"{evidence_id}: {path}")

    def test_pages_have_canonical_language_open_graph_and_skip_navigation(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            english = (output / "runtime/index.html").read_text(encoding="utf-8")
            chinese = (output / "zh-TW/runtime/index.html").read_text(encoding="utf-8")

            self.assertIn('<html lang="en">', english)
            self.assertIn('<html lang="zh-Hant">', chinese)
            self.assertIn(
                '<link rel="canonical" href="https://apr.evemisslab.com/runtime/">',
                english,
            )
            self.assertIn('hreflang="zh-Hant"', english)
            self.assertIn('hreflang="en"', chinese)
            self.assertIn('<meta property="og:type" content="website">', english)
            self.assertIn(
                '<meta property="og:url" content="https://apr.evemisslab.com/runtime/">',
                english,
            )
            self.assertIn('class="skip-link"', english)
            self.assertIn('id="main"', english)
            self.assertIn('aria-label="Primary navigation"', english)
            self.assertIn('aria-current="page"', english)

    def test_chinese_brand_navigation_stays_in_locale(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            chinese = (output / "zh-TW/index.html").read_text(encoding="utf-8")

            self.assertIn('<a class="brand" href="/zh-TW/" aria-label="APR 首頁">', chinese)
            self.assertIn("感知 · 驗證 · 復原", chinese)

    def test_lab_has_six_labelled_controls_and_live_educational_projection(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            for prefix, locale, legends, notice in (
                (
                    Path(),
                    "en",
                    (
                        "Evidence freshness",
                        "Uncertainty",
                        "Action risk",
                        "Evidence conflict",
                        "Observation budget",
                        "Goal evidence",
                    ),
                    "Educational projection only",
                ),
                (
                    Path("zh-TW"),
                    "zh-TW",
                    ("證據新鮮度", "不確定性", "行動風險", "證據衝突", "觀察預算", "目標證據"),
                    "僅供教育投影",
                ),
            ):
                lab = (output / prefix / "lab/index.html").read_text(encoding="utf-8")
                self.assertIn(f'<form class="apr-lab" data-apr-lab data-locale="{locale}"', lab)
                self.assertEqual(6, lab.count("<fieldset data-control="))
                self.assertEqual(12, lab.count('<label class="lab-choice">'))
                for legend in legends:
                    self.assertIn(f"<legend>{legend}</legend>", lab)
                self.assertEqual(1, lab.count('data-lab-output aria-live="polite"'))
                self.assertIn("data-lab-notice", lab)
                self.assertIn(notice, lab)
                self.assertIn('<script type="module" src="/assets/app.js"></script>', lab)

    def test_client_has_no_remote_or_local_runtime_endpoint(self):
        script = (ROOT / "site/src/assets/app.js").read_text(encoding="utf-8")
        for forbidden in (
            "localhost",
            "127.0.0.1",
            "api.openai.com",
            "anthropic.com",
            "aiplatform.googleapis.com",
        ):
            self.assertNotIn(forbidden, script)
        self.assertIn("/data/demo-scenarios.json", script)
        self.assertIn("export function scenarioKey(state)", script)
        self.assertIn("export function renderScenario(output, row, labels)", script)
        self.assertNotIn("innerHTML", script)

    def test_public_copy_does_not_claim_open_source_or_production_readiness(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            joined = "\n".join(path.read_text(encoding="utf-8") for path in output.rglob("*.html"))
            self.assertNotIn("production-ready", joined.lower())
            self.assertNotIn("open-source licence", joined.lower())

    def test_locales_keep_mcp_claims_within_the_available_evidence_boundary(self):
        content = load_content()
        for locale, planned in (
            ("en", "planned and not implemented"),
            ("zh-TW", "規劃中且尚未實作"),
        ):
            mcp = content.PAGES[locale]["mcp"]
            mcp_copy = " ".join(
                [mcp["heading"], mcp["summary"], *(section["body"] for section in mcp["sections"])]
            )
            self.assertIn(planned, mcp_copy)
            self.assertNotIn("stdio", mcp_copy)
            self.assertNotIn("loopback", mcp_copy)

    def test_locales_describe_exported_lab_matrix_and_interface_as_current(self):
        content = load_content()
        for locale, current_matrix, current_controls, current_interface, deferred_ui in (
            (
                "en",
                "The exported scenario matrix reports",
                "local lookup controls are available below",
                "local interface renders those fields below",
                "will be added",
            ),
            (
                "zh-TW",
                "匯出的情境矩陣列出",
                "本機查表控制項已在下方提供",
                "本機介面在下方呈現這些欄位",
                "將在",
            ),
        ):
            lab = content.PAGES[locale]["lab"]
            lab_copy = " ".join([lab["summary"], *(section["body"] for section in lab["sections"])])
            self.assertIn(current_matrix, lab_copy)
            self.assertIn(current_controls, lab_copy)
            self.assertIn(current_interface, lab_copy)
            self.assertNotIn(deferred_ui, lab_copy)

    def test_each_locale_has_truthful_mcp_and_release_candidate_messages(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            for _locale, prefix, release_candidate in (
                ("en", Path(), "release candidate"),
                ("zh-TW", Path("zh-TW"), "發布候選版"),
            ):
                mcp = (output / prefix / "mcp/index.html").read_text(encoding="utf-8")
                status = (output / prefix / "status/index.html").read_text(encoding="utf-8")
                self.assertIn("not_implemented", mcp)
                self.assertIn(release_candidate, status.lower())

    def test_built_css_contains_accessible_apr_visual_system(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            css = (output / "assets/styles.css").read_text(encoding="utf-8")

            for token in (
                "--canvas: #07090d;",
                "--surface: #10151d;",
                "--ink: #f2f6fb;",
                "--muted: #a7b0bd;",
                "--line: #27313d;",
                "--observe: #4cd8e8;",
                "--budget: #f5c451;",
                "--uncertain: #a78bfa;",
                "--verified: #59d88e;",
                "--danger: #ff6b8a;",
                "--shell: 72rem;",
            ):
                self.assertIn(token, css)
            self.assertIn(":focus-visible", css)
            self.assertIn("@media (prefers-reduced-motion: reduce)", css)
            self.assertIn("min-height: 40px", css)
            self.assertIn("@media (max-width:", css)
            self.assertIn(".lab-choice {", css)
            self.assertIn(".lab-output dl {", css)
            self.assertIn(".lab-output dd {", css)
