import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import Evidence, EvidenceArchive, Modality


class ArchiveTests(unittest.TestCase):
    def test_archive_persists_metadata_and_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = EvidenceArchive(tmp)
            asset = archive.store_asset(b"abc", extension=".bin")
            ev = Evidence(
                claim_key="x",
                observed_value={"value": 1},
                modality=Modality.VISION,
                source="test",
                confidence=0.9,
                cost=2.0,
                pointer=str(asset),
                metadata={"a": 1},
            )
            archive.record(ev, asset_path=asset)

            row = archive.get(ev.id)
            self.assertEqual(row["claim_key"], "x")
            self.assertEqual(row["observed_value"], {"value": 1})
            self.assertEqual(row["metadata"], {"a": 1})
            self.assertTrue(Path(row["asset_path"]).exists())


if __name__ == "__main__":
    unittest.main()
