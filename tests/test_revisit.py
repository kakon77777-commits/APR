import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    Evidence,
    EvidenceArchive,
    EvidenceStore,
    FactStatus,
    HistoricalRevisitService,
    Modality,
    RuleSemanticInspector,
    SemanticFact,
    SemanticResult,
    WorldState,
)


def semantics(image_path, prompt, context):
    return SemanticResult(
        summary="Archived image supports HIGH.",
        confidence=0.98,
        facts=[
            SemanticFact(
                key="warning.severity",
                value="high",
                confidence=0.98,
                volatile=False,
                ttl=100,
            )
        ],
    )


class HistoricalRevisitTests(unittest.TestCase):
    def test_revisit_uses_archived_asset_and_resolves_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = EvidenceArchive(tmp)
            store = EvidenceStore()
            world = WorldState(store)
            world.configure_fact("warning.severity", volatile=False, ttl=100)

            asset = archive.store_asset(b"fakepng", extension=".png")
            old = Evidence(
                "warning.severity",
                "low",
                Modality.VISION,
                "old",
                0.9,
                2.0,
                pointer=str(asset),
            )
            world.revise(old)
            archive.record(old, asset_path=asset)

            new = Evidence(
                "warning.severity",
                "high",
                Modality.VISION,
                "new",
                0.95,
                2.0,
            )
            world.revise(new)
            self.assertEqual(
                world.get("warning.severity").status,
                FactStatus.CONTRADICTED,
            )

            service = HistoricalRevisitService(
                world,
                archive,
                RuleSemanticInspector(semantics),
            )
            record = service.revisit("warning.severity")

            self.assertEqual(record.asset_path, asset.resolve())
            self.assertTrue(record.resolved)
            fact = world.get("warning.severity")
            self.assertEqual(fact.value, "high")
            self.assertEqual(fact.status, FactStatus.KNOWN)

            rows = archive.for_claim("warning.severity")
            self.assertTrue(any(row["metadata"].get("historical_revisit") for row in rows))

    def test_revisit_without_asset_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = EvidenceArchive(tmp)
            store = EvidenceStore()
            world = WorldState(store)
            ev = Evidence(
                "x",
                1,
                Modality.STRUCTURED,
                "source",
                0.9,
                0.1,
            )
            world.revise(ev)
            archive.record(ev)

            service = HistoricalRevisitService(
                world,
                archive,
                RuleSemanticInspector(semantics),
            )
            with self.assertRaises(LookupError):
                service.revisit("x")


if __name__ == "__main__":
    unittest.main()
