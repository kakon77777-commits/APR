import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    EvidenceArchive,
    EvidenceStore,
    RuleSemanticInspector,
    ScreenFrame,
    SemanticEvidencePipeline,
    SemanticFact,
    SemanticResult,
    StreamEvent,
    WorldState,
)


def frame(width=20, height=20):
    px = bytes([0, 0, 0, 255])
    return ScreenFrame(width, height, px * (width * height))


def semantics(image_path, prompt, context):
    return SemanticResult(
        summary="Button appeared.",
        confidence=0.9,
        facts=[
            SemanticFact(
                key="desktop.button.visible",
                value=True,
                confidence=0.95,
                volatile=True,
                ttl=5,
            )
        ],
    )


class SemanticPipelineTests(unittest.TestCase):
    def test_semantic_roi_is_archived_and_updates_world(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore()
            world = WorldState(store)
            archive = EvidenceArchive(tmp)
            inspector = RuleSemanticInspector(semantics)
            pipeline = SemanticEvidencePipeline(world, archive, inspector)

            event = StreamEvent(
                kind="screen_change",
                target="desktop.screen",
                significance=0.8,
                value=0.2,
                metadata={"bbox": (5, 5, 12, 12)},
            )
            record = pipeline.inspect_screen_event(event, frame())

            self.assertTrue(record.crop_path.exists())
            self.assertEqual(
                world.get("desktop.button.visible").value,
                True,
            )
            self.assertEqual(
                world.get("desktop.screen.semantic_summary").value,
                "Button appeared.",
            )
            self.assertGreaterEqual(len(record.evidence_ids), 2)
            rows = archive.for_claim("desktop.button.visible")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["asset_path"], str(record.crop_path.resolve()))


if __name__ == "__main__":
    unittest.main()
