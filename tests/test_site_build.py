from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
