import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    EventLedger,
    Evidence,
    EvidenceArchive,
    EvidenceStore,
    Modality,
    NativeEvent,
    RetentionManager,
    RetentionPolicy,
    WorldState,
)


class RetentionTests(unittest.TestCase):
    def test_retention_keeps_world_referenced_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = time.time()
            ledger = EventLedger(Path(tmp) / "events.sqlite3")
            archive = EvidenceArchive(Path(tmp) / "archive")
            world = WorldState(EvidenceStore())

            ledger.append(
                NativeEvent(
                    kind="noise",
                    source="test",
                    target="x",
                    significance=0.1,
                    timestamp=now - 1000,
                )
            )
            asset = archive.store_asset(b"asset", extension=".bin")
            protected = Evidence(
                claim_key="important",
                observed_value=1,
                modality=Modality.VISION,
                source="test",
                confidence=0.4,
                cost=1.0,
                timestamp=now - 1000,
                pointer=str(asset),
            )
            world.revise(protected)
            archive.record(protected, asset_path=asset)

            unprotected = Evidence(
                claim_key="old.noise",
                observed_value=2,
                modality=Modality.VISION,
                source="test",
                confidence=0.4,
                cost=1.0,
                timestamp=now - 1000,
            )
            archive.record(unprotected)

            manager = RetentionManager(
                ledger,
                archive,
                world,
                policy=RetentionPolicy(
                    event_keep_seconds=100,
                    event_keep_significance_at_least=0.75,
                    evidence_keep_seconds=100,
                    evidence_keep_confidence_at_least=0.9,
                ),
            )
            report = manager.run(now=now)
            self.assertEqual(report.events_deleted, 1)
            self.assertEqual(report.evidence_deleted, 1)
            self.assertIsNotNone(archive.get(protected.id))
            self.assertIsNone(archive.get(unprotected.id))
            self.assertTrue(asset.exists())

    def test_unreferenced_asset_is_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = time.time()
            ledger = EventLedger(Path(tmp) / "events.sqlite3")
            archive = EvidenceArchive(Path(tmp) / "archive")
            asset = archive.store_asset(b"old", extension=".bin")
            ev = Evidence(
                claim_key="old",
                observed_value=True,
                modality=Modality.VISION,
                source="test",
                confidence=0.2,
                cost=1.0,
                timestamp=now - 1000,
            )
            archive.record(ev, asset_path=asset)
            manager = RetentionManager(
                ledger,
                archive,
                None,
                policy=RetentionPolicy(
                    evidence_keep_seconds=100, evidence_keep_confidence_at_least=0.9
                ),
            )
            report = manager.run(now=now)
            self.assertEqual(report.evidence_deleted, 1)
            self.assertEqual(report.assets_deleted, 1)
            self.assertFalse(asset.exists())


if __name__ == "__main__":
    unittest.main()
