from __future__ import annotations

import copy
import html as html_module
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = ROOT / "site/src/content.py"
BUILD_PATH = ROOT / "site/build.py"


def load_content():
    spec = importlib.util.spec_from_file_location("apr_site_content", CONTENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load site content from {CONTENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_build():
    spec = importlib.util.spec_from_file_location("apr_site_build", BUILD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load site builder from {BUILD_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def snapshot_tree(root: Path) -> dict[str, tuple[str, bytes]]:
    snapshot: dict[str, tuple[str, bytes]] = {}
    if not root.exists():
        return snapshot
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            snapshot[relative] = ("directory", b"")
        elif path.is_file():
            snapshot[relative] = ("file", path.read_bytes())
    return snapshot


class SiteBuildTests(unittest.TestCase):
    def build(self, output: Path) -> None:
        subprocess.run(
            [sys.executable, "-B", "site/build.py", "--output", str(output)],
            cwd=ROOT,
            check=True,
        )

    def assert_generated_index_mutation_is_rejected(self, mutate) -> None:
        build = load_build()
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            output = parent / "owned-output"
            build.build(output)

            index_path = output / "ai/site.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            mutate(index)
            index_path.write_text(
                json.dumps(index, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (output / "keep.bin").write_bytes(b"\x00preserve-mutated-output\xff")
            before = snapshot_tree(output)

            error = None
            try:
                build.build(output)
            except ValueError as exc:
                error = str(exc)

            self.assertIsNotNone(error, "a noncanonical generated index was accepted as owned")
            self.assertIn("refusing to replace non-empty unowned output", error)
            self.assertEqual(before, snapshot_tree(output))
            self.assertEqual({output}, set(parent.iterdir()))

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

    def test_default_output_is_repository_site_dist_independent_of_cwd(self):
        build = load_build()
        previous_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as raw:
            try:
                os.chdir(raw)
                with mock.patch.object(sys, "argv", ["site/build.py"]):
                    args = build.parse_args()
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(ROOT / "site/dist", args.output)

    def test_protected_roots_and_their_ancestors_are_rejected_before_mutation(self):
        build = load_build()

        class MutationAttempt(RuntimeError):
            pass

        protected = {
            build.ROOT,
            build.ROOT / "site",
            build.SOURCE,
            build.PUBLIC,
            build.ROOT / ".git",
        }
        candidates = protected | {parent for path in protected for parent in path.parents}

        def mutation_attempt(*_args, **_kwargs):
            raise MutationAttempt("the builder attempted mutation before rejecting the output")

        for candidate in sorted(candidates, key=str):
            with self.subTest(candidate=candidate):
                with (
                    mock.patch.object(build.shutil, "rmtree", side_effect=mutation_attempt),
                    mock.patch.object(build.shutil, "copyfile", side_effect=mutation_attempt),
                    mock.patch.object(Path, "mkdir", side_effect=mutation_attempt),
                    mock.patch.object(Path, "write_text", side_effect=mutation_attempt),
                ):
                    try:
                        build.build(candidate)
                    except ValueError:
                        pass
                    except MutationAttempt as exc:
                        self.fail(str(exc))
                    else:
                        self.fail(f"protected output was accepted: {candidate}")

    def test_source_public_and_git_metadata_descendants_are_rejected_before_mutation(self):
        build = load_build()

        class MutationAttempt(RuntimeError):
            pass

        def mutation_attempt(*_args, **_kwargs):
            raise MutationAttempt("the builder attempted mutation before rejecting the output")

        candidates = (
            build.SOURCE / "assets",
            build.PUBLIC / "generated-child",
            *(path / "generated-child" for path in build._git_metadata_paths()),
        )

        for candidate in candidates:
            with self.subTest(candidate=candidate):
                with (
                    mock.patch.object(build.shutil, "rmtree", side_effect=mutation_attempt),
                    mock.patch.object(build.shutil, "copyfile", side_effect=mutation_attempt),
                    mock.patch.object(Path, "mkdir", side_effect=mutation_attempt),
                    mock.patch.object(Path, "write_text", side_effect=mutation_attempt),
                ):
                    try:
                        build.build(candidate)
                    except ValueError:
                        pass
                    except MutationAttempt as exc:
                        self.fail(str(exc))
                    else:
                        self.fail(f"protected descendant was accepted: {candidate}")

    def test_non_empty_unowned_output_is_rejected_and_preserved_byte_for_byte(self):
        build = load_build()
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "unowned"
            (output / "ai").mkdir(parents=True)
            (output / "ai/site.json").write_text('{"schema":"other-site/v1"}\n', encoding="utf-8")
            (output / "keep.bin").write_bytes(b"\x00keep-this-output\xff")
            before = snapshot_tree(output)

            try:
                build.build(output)
            except ValueError:
                pass
            else:
                self.fail("a non-empty unowned output directory was rebuilt")

            self.assertEqual(before, snapshot_tree(output))

    def test_generated_index_must_exactly_match_canonical_ownership_contract(self):
        mutations = (
            ("missing_top_level_site", lambda index: index.pop("site")),
            ("extra_top_level_field", lambda index: index.__setitem__("owner", "other")),
            ("missing_site_field", lambda index: index["site"].pop("version")),
            ("extra_site_field", lambda index: index["site"].__setitem__("owner", "other")),
            ("wrong_site_name", lambda index: index["site"].__setitem__("name", "Other")),
            (
                "wrong_site_origin",
                lambda index: index["site"].__setitem__("origin", "https://example.invalid"),
            ),
            ("wrong_site_version", lambda index: index["site"].__setitem__("version", "9.9.9")),
            (
                "wrong_site_source_ref",
                lambda index: index["site"].__setitem__("source_ref", "0" * 40),
            ),
            (
                "wrong_site_release_status",
                lambda index: index["site"].__setitem__("release_status", "live"),
            ),
            (
                "source_ref_wrong_shape",
                lambda index: index["site"].__setitem__("source_ref", ["0" * 40]),
            ),
            ("missing_route_record", lambda index: index["pages"].pop()),
            (
                "extra_route_record",
                lambda index: index["pages"].append(copy.deepcopy(index["pages"][0])),
            ),
            (
                "duplicate_route_record",
                lambda index: index["pages"].__setitem__(-1, copy.deepcopy(index["pages"][0])),
            ),
            ("missing_page_field", lambda index: index["pages"][0].pop("path")),
            (
                "extra_page_field",
                lambda index: index["pages"][0].__setitem__("owner", "other"),
            ),
            (
                "title_drift",
                lambda index: index["pages"][0].__setitem__("title", "Drifted title"),
            ),
            (
                "description_drift",
                lambda index: index["pages"][0].__setitem__("description", "Drifted description"),
            ),
            (
                "arbitrary_page_path",
                lambda index: index["pages"][0].__setitem__("path", "other/index.html"),
            ),
            (
                "traversal_page_path",
                lambda index: index["pages"][0].__setitem__("path", "../escape/index.html"),
            ),
            (
                "arbitrary_url",
                lambda index: index["pages"][0].__setitem__("url", "https://example.invalid/"),
            ),
            (
                "noncanonical_url",
                lambda index: index["pages"][0].__setitem__(
                    "url", "https://apr.evemisslab.com/other/"
                ),
            ),
            (
                "empty_evidence_ids",
                lambda index: index["pages"][0].__setitem__("evidence_ids", []),
            ),
            (
                "unknown_evidence_id",
                lambda index: index["pages"][0].__setitem__("evidence_ids", ["unknown_evidence"]),
            ),
            (
                "reordered_evidence_ids",
                lambda index: index["pages"][0]["evidence_ids"].reverse(),
            ),
            (
                "drifted_evidence_ids",
                lambda index: index["pages"][0]["evidence_ids"].__setitem__(0, "event_runtime"),
            ),
            (
                "locale_mismatch",
                lambda index: index["pages"][0].__setitem__("locale", "zh-TW"),
            ),
            (
                "slug_mismatch",
                lambda index: index["pages"][0].__setitem__("slug", "runtime"),
            ),
        )

        for name, mutate in mutations:
            with self.subTest(mutation=name):
                self.assert_generated_index_mutation_is_rejected(mutate)

    def test_empty_existing_output_can_be_built_without_rmtree_on_the_caller_path(self):
        build = load_build()
        original_rmtree = build.shutil.rmtree
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            output = parent / "empty-output"
            output.mkdir()

            def guarded_rmtree(path, *args, **kwargs):
                if Path(path) == output:
                    raise AssertionError("rmtree called on caller-selected output")
                return original_rmtree(path, *args, **kwargs)

            try:
                with mock.patch.object(build.shutil, "rmtree", side_effect=guarded_rmtree):
                    build.build(output)
            except AssertionError as exc:
                self.fail(str(exc))

            self.assertTrue((output / "ai/site.json").is_file())
            self.assertEqual({output}, set(parent.iterdir()))

    def test_owned_output_rebuild_removes_stale_files_without_rmtree_on_output(self):
        build = load_build()
        original_rmtree = build.shutil.rmtree
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            output = parent / "owned-output"
            build.build(output)
            (output / "stale.bin").write_bytes(b"stale")

            def guarded_rmtree(path, *args, **kwargs):
                if Path(path) == output:
                    raise AssertionError("rmtree called on caller-selected output")
                return original_rmtree(path, *args, **kwargs)

            try:
                with mock.patch.object(build.shutil, "rmtree", side_effect=guarded_rmtree):
                    build.build(output)
            except AssertionError as exc:
                self.fail(str(exc))

            self.assertFalse((output / "stale.bin").exists())
            expected_files = {
                "index.html",
                "runtime/index.html",
                "lab/index.html",
                "papers/index.html",
                "mcp/index.html",
                "status/index.html",
                "zh-TW/index.html",
                "zh-TW/runtime/index.html",
                "zh-TW/lab/index.html",
                "zh-TW/papers/index.html",
                "zh-TW/mcp/index.html",
                "zh-TW/status/index.html",
                "assets/app.js",
                "assets/styles.css",
                "ai/site.json",
                "data/demo-scenarios.json",
                "llms.txt",
                "sitemap.xml",
                "robots.txt",
                "404.html",
                "_headers",
                "favicon.svg",
            }
            self.assertEqual(
                set(),
                {relative for relative in expected_files if not (output / relative).is_file()},
            )
            self.assertEqual({output}, set(parent.iterdir()))

    def test_invalid_generation_preserves_previous_output_byte_for_byte(self):
        build = load_build()
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            output = parent / "owned-output"
            build.build(output)
            before = snapshot_tree(output)

            with mock.patch.object(build, "export_scenarios", return_value={}):
                with self.assertRaises(ValueError):
                    build.build(output)

            self.assertEqual(before, snapshot_tree(output))
            self.assertEqual({output}, set(parent.iterdir()))

    def test_failed_final_rename_restores_previous_output_and_cleans_siblings(self):
        build = load_build()
        original_replace = Path.replace
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            output = parent / "owned-output"
            build.build(output)
            before = snapshot_tree(output)
            failure_injected = False

            def replace_with_one_failure(path, target):
                nonlocal failure_injected
                if Path(target) == output and not failure_injected:
                    failure_injected = True
                    raise OSError("simulated final rename failure")
                return original_replace(path, target)

            with mock.patch.object(Path, "replace", replace_with_one_failure):
                with self.assertRaisesRegex(OSError, "simulated final rename failure"):
                    build.build(output)

            self.assertTrue(failure_injected)
            self.assertEqual(before, snapshot_tree(output))
            self.assertEqual({output}, set(parent.iterdir()))

    def test_generated_human_pages_and_404_use_the_same_origin_svg_favicon(self):
        favicon_link = '<link rel="icon" href="/favicon.svg" type="image/svg+xml">'
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            pages = [output / "404.html"]
            for locale in ("", "zh-TW"):
                for route in ("", "runtime", "lab", "papers", "mcp", "status"):
                    pages.append(output / locale / route / "index.html")
            for page in pages:
                self.assertIn(favicon_link, page.read_text(encoding="utf-8"), page)
            self.assertTrue((output / "favicon.svg").is_file(), "favicon.svg")

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

    def test_generated_app_javascript_bytes_equal_the_source_asset(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            self.assertEqual(
                (ROOT / "site/src/assets/app.js").read_bytes(),
                (output / "assets/app.js").read_bytes(),
            )

    def test_machine_index_is_valid_json(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            data = json.loads((output / "ai/site.json").read_text(encoding="utf-8"))
            self.assertEqual("apr-site-index/v1", data["schema"])

    def test_machine_surfaces_share_content_identifiers_and_canonical_urls(self):
        content = load_content()
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)

            for relative in (
                "llms.txt",
                "ai/site.json",
                "sitemap.xml",
                "robots.txt",
                "404.html",
                "_headers",
            ):
                self.assertTrue((output / relative).is_file(), relative)

            index = json.loads((output / "ai/site.json").read_text(encoding="utf-8"))
            pages = {(page["locale"], page["slug"]): page for page in index["pages"]}
            llms = (output / "llms.txt").read_text(encoding="utf-8")
            for locale in content.LOCALES:
                for route in content.ROUTES:
                    key = (locale, route.slug)
                    segments = [
                        part
                        for part in (
                            "zh-TW" if locale == "zh-TW" else "",
                            route.slug,
                        )
                        if part
                    ]
                    canonical = content.SITE["origin"] + "/" + "/".join(segments)
                    if segments:
                        canonical += "/"
                    self.assertEqual(route.title[locale], pages[key]["title"])
                    self.assertEqual(route.description[locale], pages[key]["description"])
                    self.assertEqual(canonical, pages[key]["url"])
                    self.assertEqual(
                        list(content.PAGES[locale][route.slug]["evidence_ids"]),
                        pages[key]["evidence_ids"],
                    )
                    self.assertIn(route.title[locale], llms)
                    self.assertIn(canonical, llms)

    def test_sitemap_robots_and_bilingual_404_are_bounded(self):
        content = load_content()
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)

            self.assertTrue((output / "sitemap.xml").is_file(), "sitemap.xml")
            self.assertTrue((output / "robots.txt").is_file(), "robots.txt")
            self.assertTrue((output / "404.html").is_file(), "404.html")
            sitemap = ET.parse(output / "sitemap.xml")
            namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = {element.text for element in sitemap.findall("sm:url/sm:loc", namespace)}
            expected = {
                content.SITE["origin"]
                + ("/zh-TW" if locale == "zh-TW" else "")
                + (f"/{route.slug}" if route.slug else "")
                + ("/" if locale == "zh-TW" or route.slug else "/")
                for locale in content.LOCALES
                for route in content.ROUTES
            }
            self.assertEqual(expected, urls)
            self.assertNotIn(f"{content.SITE['origin']}/404.html", urls)

            robots = (output / "robots.txt").read_text(encoding="utf-8")
            self.assertEqual(
                f"User-agent: *\nAllow: /\nSitemap: {content.SITE['origin']}/sitemap.xml\n",
                robots,
            )
            not_found = (output / "404.html").read_text(encoding="utf-8")
            self.assertIn('<meta name="robots" content="noindex">', not_found)
            self.assertIn('href="/"', not_found)
            self.assertIn('href="/zh-TW/"', not_found)
            self.assertIn("Page not found", not_found)
            self.assertIn("找不到頁面", not_found)

    def test_security_headers_are_copied_and_restrict_connections(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            self.assertTrue((output / "_headers").is_file(), "_headers")
            headers = (output / "_headers").read_text(encoding="utf-8")
            self.assertIn("Content-Security-Policy:", headers)
            self.assertIn("default-src 'self'", headers)
            self.assertIn("connect-src 'self'", headers)
            self.assertIn("object-src 'none'", headers)
            self.assertIn("form-action 'none'", headers)
            self.assertIn("frame-ancestors 'none'", headers)
            self.assertIn("Referrer-Policy: no-referrer", headers)
            self.assertIn("X-Content-Type-Options: nosniff", headers)
            self.assertIn(
                "Cache-Control: public, max-age=0, must-revalidate, no-transform", headers
            )

    def test_public_copy_is_recursive_and_rejects_generated_collisions(self):
        build = load_build()
        self.assertTrue(hasattr(build, "copy_public"), "site builder must expose copy_public")
        with (
            tempfile.TemporaryDirectory() as public_raw,
            tempfile.TemporaryDirectory() as output_raw,
        ):
            public = Path(public_raw)
            output = Path(output_raw)
            (public / "nested").mkdir()
            (public / "nested/policy.txt").write_text("bounded\n", encoding="utf-8")
            build.copy_public(public, output)
            self.assertEqual(
                "bounded\n", (output / "nested/policy.txt").read_text(encoding="utf-8")
            )
            (public / "nested/policy.txt").unlink()
            (public / "nested").rmdir()
            (output / "nested/policy.txt").unlink()
            (output / "nested").rmdir()

            (public / "ai").mkdir()
            (public / "ai/site.json").write_text("collision\n", encoding="utf-8")
            (output / "ai").mkdir()
            (output / "ai/site.json").write_text("generated\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                build.copy_public(public, output)
            self.assertEqual("generated\n", (output / "ai/site.json").read_text(encoding="utf-8"))

    def test_generated_artifact_has_no_windows_absolute_path(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            joined = b"\n".join(path.read_bytes() for path in output.rglob("*") if path.is_file())
            self.assertNotRegex(joined.decode("utf-8", errors="ignore"), r"[A-Za-z]:\\")

    def test_site_package_pins_wrangler_and_validates_client_behavior(self):
        package_path = ROOT / "site/package.json"
        self.assertTrue(package_path.is_file(), package_path)
        package = json.loads(package_path.read_text(encoding="utf-8"))
        self.assertEqual("apr-evemisslab-site", package["name"])
        self.assertTrue(package["private"])
        self.assertEqual("0.10.0", package["version"])
        self.assertEqual("module", package.get("type"))
        self.assertEqual({"wrangler": "4.125.0"}, package["devDependencies"])
        self.assertEqual("python build.py --output dist", package["scripts"]["build"])
        self.assertEqual(
            "cd .. && node --test tests/site_app.test.mjs",
            package["scripts"]["test:client"],
        )
        self.assertEqual(
            "npm run build && npm run test:client",
            package["scripts"]["validate"],
        )
        self.assertEqual(
            "npm run validate && wrangler deploy --dry-run",
            package["scripts"]["deploy:dry"],
        )
        self.assertEqual("npm run validate && wrangler deploy", package["scripts"]["deploy"])

    def test_wrangler_config_is_entrypoint_free_assets_only_and_has_no_binding(self):
        config_path = ROOT / "site/wrangler.jsonc"
        self.assertTrue(config_path.is_file(), config_path)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual({"$schema", "name", "compatibility_date", "assets", "routes"}, set(config))
        self.assertEqual("node_modules/wrangler/config-schema.json", config["$schema"])
        self.assertEqual("apr-evemisslab", config["name"])
        self.assertEqual("2026-08-24", config["compatibility_date"])
        self.assertEqual(
            {"directory": "./dist", "not_found_handling": "404-page"}, config["assets"]
        )
        self.assertEqual(
            [{"pattern": "apr.evemisslab.com", "custom_domain": True}], config["routes"]
        )

    def test_ci_installs_node_and_runs_the_package_client_test(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("actions/setup-node@", workflow)
        self.assertIn('node-version: "24"', workflow)
        self.assertIn("npm ci --prefix site", workflow)
        self.assertIn("npm run test:client --prefix site", workflow)

    def test_ci_and_readme_use_the_exact_site_inclusive_ruff_scope(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for command in (
            "ruff format --check apr_runtime tests examples site",
            "ruff check apr_runtime tests examples site",
        ):
            self.assertIn(command, workflow)
            self.assertIn(command, readme)

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

    def test_lab_embeds_the_selected_content_value_map_as_inert_form_data(self):
        content = load_content()
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            for locale, relative in (
                ("en", Path("lab/index.html")),
                ("zh-TW", Path("zh-TW/lab/index.html")),
            ):
                rendered = (output / relative).read_text(encoding="utf-8")
                match = re.search(r'data-value-labels="([^"]+)"', rendered)
                self.assertIsNotNone(match, locale)
                encoded = html_module.unescape(match.group(1))
                self.assertEqual(content.LAB_UI[locale]["value_labels"], json.loads(encoded))
                self.assertNotIn('<script type="application/json"', rendered)

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
        self.assertIn("export function renderScenario(output, row, labels, valueLabels)", script)
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
        for (
            locale,
            current_matrix,
            current_controls,
            current_interface,
            inaccurate_ui,
            deferred_ui,
        ) in (
            (
                "en",
                "The exported scenario matrix reports",
                "local lookup controls are available below",
                "the local interface renders disposition, reason, effective fact status, "
                "selected channel, budget before and projected after, affordability, and "
                "action-gate state below",
                "local interface renders those fields below",
                "will be added",
            ),
            (
                "zh-TW",
                "匯出的情境矩陣列出",
                "本機查表控制項已在下方提供",
                "本機介面在下方呈現處置、理由、有效事實狀態、所選通道、預算前值與預估後值、"
                "可負擔性，以及行動閘門狀態",
                "本機介面在下方呈現這些欄位",
                "將在",
            ),
        ):
            lab = content.PAGES[locale]["lab"]
            lab_copy = " ".join([lab["summary"], *(section["body"] for section in lab["sections"])])
            self.assertIn(current_matrix, lab_copy)
            self.assertIn(current_controls, lab_copy)
            self.assertIn(current_interface, lab_copy)
            self.assertNotIn(inaccurate_ui, lab_copy)
            self.assertNotIn(deferred_ui, lab_copy)

    def test_each_locale_has_truthful_mcp_release_candidate_and_live_site_messages(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            for _locale, prefix, release_candidate, live_site, stale_site_claim in (
                (
                    "en",
                    Path(),
                    "release candidate",
                    "Live public site",
                    "live deployment not yet claimed",
                ),
                (
                    "zh-TW",
                    Path("zh-TW"),
                    "發布候選版",
                    "公開網站已上線",
                    "尚未宣稱正式上線",
                ),
            ):
                mcp = (output / prefix / "mcp/index.html").read_text(encoding="utf-8")
                status = (output / prefix / "status/index.html").read_text(encoding="utf-8")
                self.assertIn("not_implemented", mcp)
                self.assertIn(release_candidate, status.lower())
                self.assertIn(live_site, status)
                self.assertNotIn(stale_site_claim, status)

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
