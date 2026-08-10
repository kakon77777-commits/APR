import re
import unittest
from pathlib import Path
from urllib.parse import unquote

import apr_runtime

ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"\[[^]]+\]\(([^)]+)\)")


class RepositoryIntegrityTests(unittest.TestCase):
    def test_public_exports_resolve(self):
        missing = sorted(name for name in apr_runtime.__all__ if not hasattr(apr_runtime, name))
        self.assertEqual(missing, [])

    def test_local_document_links_exist(self):
        documents = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
        missing = []
        for document in documents:
            text = document.read_text(encoding="utf-8")
            for target in LINK_PATTERN.findall(text):
                if "://" in target or target.startswith(("#", "mailto:")):
                    continue
                path_text = unquote(target.split("#", 1)[0])
                if not path_text:
                    continue
                candidate = (document.parent / path_text).resolve()
                if not candidate.exists():
                    missing.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
