import sys
import tempfile
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


def solid_frame(width, height, value):
    px = bytes([value, value, value, 255])
    return ScreenFrame(width, height, px * (width * height))


class SequenceScreen:
    def __init__(self, frames):
        self.frames = list(frames)
        self.i = 0

    def capture(self):
        frame = self.frames[min(self.i, len(self.frames) - 1)]
        self.i += 1
        return frame


def fake_semantics(image_path, prompt, context):
    return SemanticResult(
        summary="A warning dialog appeared in the changed screen region.",
        confidence=0.93,
        facts=[
            SemanticFact(
                key="desktop.warning.visible",
                value=True,
                confidence=0.96,
                volatile=True,
                ttl=5.0,
                metadata={"kind": "warning_dialog"},
            ),
            SemanticFact(
                key="desktop.warning.severity",
                value="high",
                confidence=0.88,
                volatile=True,
                ttl=5.0,
            ),
        ],
    )


def run(data: Path):
    w, h = 80, 50
    base = solid_frame(w, h, 0)
    raw = bytearray(base.bgra)

    # Add a bright "dialog" block.
    for y in range(12, 38):
        for x in range(18, 64):
            i = (y * w + x) * 4
            raw[i : i + 4] = bytes([230, 230, 230, 255])
    changed = ScreenFrame(w, h, bytes(raw))

    store = EvidenceStore()
    world = WorldState(store)

    monitor = RealStreamMonitor(
        world,
        screen_source=SequenceScreen([base, changed]),
        config=RealStreamConfig(
            screen_change_threshold=0.02,
            screen_goal_relevance=0.9,
        ),
    )

    archive = EvidenceArchive(data)
    inspector = RuleSemanticInspector(fake_semantics)
    pipeline = SemanticEvidencePipeline(world, archive, inspector)
    runtime = SemanticStreamRuntime(
        monitor,
        pipeline,
        config=SemanticStreamConfig(escalation_threshold=0.20),
    )

    # Prime frame.
    runtime.tick(goal="Watch for important warnings.")

    events, inspections = runtime.tick(goal="Watch for important warnings.")

    print("events:")
    for event in events:
        print(
            " ",
            event.kind,
            f"sig={event.significance:.3f}",
            event.metadata,
        )

    print("\nsemantic inspections:")
    for record in inspections:
        print("  crop:", record.crop_path)
        print("  summary:", record.result.summary)
        print("  facts:", [(f.key, f.value) for f in record.result.facts])

    print("\nworld state:")
    for key, value in world.snapshot().items():
        if key.startswith("desktop.warning") or key.endswith("semantic_summary"):
            print(" ", key, "=>", value)

    print("\narchive rows:")
    for row in archive.recent(limit=10):
        print(" ", row["claim_key"], "->", row["asset_path"])


def main():
    with tempfile.TemporaryDirectory(prefix="apr-semantic-demo-") as tmp:
        run(Path(tmp))


if __name__ == "__main__":
    main()
