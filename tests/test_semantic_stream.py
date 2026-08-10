import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    EvidenceArchive,
    EvidenceStore,
    RealStreamConfig,
    RealStreamMonitor,
    RuleSemanticInspector,
    ScreenFrame,
    SemanticEvidencePipeline,
    SemanticFact,
    SemanticResult,
    SemanticStreamConfig,
    SemanticStreamRuntime,
    WorldState,
)


def solid(width, height, v):
    px = bytes([v, v, v, 255])
    return ScreenFrame(width, height, px * (width * height))


class SeqScreen:
    def __init__(self, values):
        self.values = values
        self.i = 0

    def capture(self):
        x = self.values[min(self.i, len(self.values) - 1)]
        self.i += 1
        return x


def semantic(image_path, prompt, context):
    return SemanticResult(
        summary="Large screen change.",
        confidence=0.9,
        facts=[
            SemanticFact(
                "desktop.scene.changed_semantically",
                True,
                0.9,
                volatile=True,
                ttl=3,
            )
        ],
    )


class SemanticStreamTests(unittest.TestCase):
    def test_only_escalated_screen_change_gets_semantic_inspection(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore()
            world = WorldState(store)
            monitor = RealStreamMonitor(
                world,
                screen_source=SeqScreen(
                    [
                        solid(20, 20, 0),
                        solid(20, 20, 255),
                    ]
                ),
                config=RealStreamConfig(
                    screen_change_threshold=0.01,
                    screen_goal_relevance=1.0,
                ),
            )
            pipeline = SemanticEvidencePipeline(
                world,
                EvidenceArchive(tmp),
                RuleSemanticInspector(semantic),
            )
            runtime = SemanticStreamRuntime(
                monitor,
                pipeline,
                config=SemanticStreamConfig(escalation_threshold=0.2),
            )

            _, first = runtime.tick()
            self.assertEqual(first, [])

            events, second = runtime.tick()
            self.assertTrue(any(e.kind == "screen_change" for e in events))
            self.assertEqual(len(second), 1)
            self.assertTrue(world.get("desktop.scene.changed_semantically").value)


if __name__ == "__main__":
    unittest.main()
