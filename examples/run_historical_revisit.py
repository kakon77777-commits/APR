import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    Evidence,
    EvidenceArchive,
    EvidenceStore,
    HistoricalRevisitService,
    Modality,
    RuleSemanticInspector,
    SemanticFact,
    SemanticResult,
    WorldState,
)


def historical_semantics(image_path, prompt, context):
    return SemanticResult(
        summary="The archived warning ROI shows severity HIGH.",
        confidence=0.97,
        facts=[
            SemanticFact(
                key="desktop.warning.severity",
                value="high",
                confidence=0.97,
                volatile=False,
                ttl=3600,
            )
        ],
    )


def run(data: Path):
    archive = EvidenceArchive(data)
    store = EvidenceStore()
    world = WorldState(store)
    world.configure_fact(
        "desktop.warning.severity",
        ttl=3600,
        volatile=False,
    )

    # Pretend v0.3 archived the exact ROI used by the original interpretation.
    asset = archive.store_asset(
        b"\x89PNG\r\n\x1a\nhistorical-demo",
        extension=".png",
        prefix="historical-warning",
    )

    original = Evidence(
        claim_key="desktop.warning.severity",
        observed_value="low",
        modality=Modality.VISION,
        source="old_semantic_model",
        confidence=0.88,
        cost=2.0,
        pointer=str(asset),
    )
    world.revise(original)
    archive.record(original, asset_path=asset)

    # A new current observation disagrees strongly.
    conflicting = Evidence(
        claim_key="desktop.warning.severity",
        observed_value="high",
        modality=Modality.VISION,
        source="new_semantic_model",
        confidence=0.95,
        cost=2.0,
    )
    world.revise(conflicting)

    print("before revisit:", world.snapshot()["desktop.warning.severity"])

    service = HistoricalRevisitService(
        world,
        archive,
        RuleSemanticInspector(historical_semantics),
    )
    record = service.revisit(
        "desktop.warning.severity",
        question="Was the original warning actually high severity?",
    )

    print("revisited asset:", record.asset_path)
    print("semantic result:", record.result.summary)
    print("resolved:", record.resolved)
    print("after revisit:", world.snapshot()["desktop.warning.severity"])

    print("\narchived history:")
    for row in archive.for_claim("desktop.warning.severity"):
        print(
            row["source"],
            row["observed_value"],
            row["metadata"].get("historical_revisit", False),
            row["asset_path"],
        )


def main():
    with tempfile.TemporaryDirectory(prefix="apr-revisit-demo-") as tmp:
        run(Path(tmp))


if __name__ == "__main__":
    main()
