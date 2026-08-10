from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .archive import EvidenceArchive
from .models import Evidence, FactStatus, Modality
from .semantic import SemanticInspector, SemanticResult
from .world_state import WorldState


@dataclass
class HistoricalRevisitRecord:
    claim_key: str
    source_evidence_id: str
    asset_path: Path
    prompt: str
    result: SemanticResult
    new_evidence_ids: List[str]
    resolved: bool


class HistoricalRevisitService:
    """
    Re-read the exact archived asset that originally supported a WorldState fact.

    This is different from "observe the world again now":
      current re-observation -> asks what is true now
      historical revisit    -> asks what the archived evidence actually showed

    The service can therefore repair a bad summary, answer a later question,
    or resolve a contradiction without replaying the entire history.
    """

    def __init__(
        self,
        world: WorldState,
        archive: EvidenceArchive,
        inspector: SemanticInspector,
    ) -> None:
        self.world = world
        self.archive = archive
        self.inspector = inspector

    def _select_source(self, claim_key: str) -> Dict:
        fact = self.world.get(claim_key)
        rows = self.archive.by_ids(fact.evidence_ids)

        rows_with_assets = [
            row for row in rows if row.get("asset_path") and Path(row["asset_path"]).exists()
        ]

        if rows_with_assets:
            return max(
                rows_with_assets,
                key=lambda row: (
                    float(row.get("confidence", 0.0)),
                    float(row.get("timestamp", 0.0)),
                ),
            )

        fallback = self.archive.best_for_claim(
            claim_key,
            require_asset=True,
        )
        if fallback is None:
            raise LookupError(f"No archived visual asset is available for claim {claim_key!r}.")
        return fallback

    def revisit(
        self,
        claim_key: str,
        *,
        question: Optional[str] = None,
    ) -> HistoricalRevisitRecord:
        source = self._select_source(claim_key)
        asset_path = Path(source["asset_path"])

        fact_before = self.world.get(claim_key)
        prompt = (
            "Re-read this archived visual evidence. "
            f"The target fact is {claim_key!r}. "
            f"The current remembered value is {fact_before.value!r} "
            f"with status={fact_before.status.value}. "
            "Determine what this historical image itself supports. "
            "Do not infer anything that is not visible in the archived evidence."
        )
        if question:
            prompt += f" Additional question: {question}"

        result = self.inspector.inspect(
            asset_path,
            prompt=prompt,
            context={
                "historical_revisit": True,
                "claim_key": claim_key,
                "source_evidence_id": source["id"],
                "source_timestamp": source["timestamp"],
                "current_value": fact_before.value,
                "current_status": fact_before.status.value,
                "question": question,
            },
        )

        matching = [fact for fact in result.facts if fact.key == claim_key]
        new_ids: List[str] = []
        resolved = False

        for semantic_fact in matching:
            self.world.configure_fact(
                claim_key,
                ttl=semantic_fact.ttl,
                volatile=semantic_fact.volatile,
            )
            evidence = Evidence(
                claim_key=claim_key,
                observed_value=semantic_fact.value,
                modality=Modality.VISION,
                source=f"{self.inspector.name}:historical_revisit",
                confidence=max(0.0, min(1.0, semantic_fact.confidence)),
                cost=float(self.inspector.estimated_cost),
                pointer=str(asset_path),
                metadata={
                    **semantic_fact.metadata,
                    "historical_revisit": True,
                    "revisit_of": source["id"],
                    "source_asset": str(asset_path),
                    "semantic_summary": result.summary,
                },
            )

            current = self.world.get(claim_key)
            if current.status == FactStatus.CONTRADICTED:
                self.world.resolve_conflict(claim_key, evidence)
            else:
                self.world.revise(evidence)

            self.archive.record(evidence, asset_path=asset_path)
            new_ids.append(evidence.id)

            now = self.world.get(claim_key)
            resolved = now.status != FactStatus.CONTRADICTED and now.confidence >= 0.85

        return HistoricalRevisitRecord(
            claim_key=claim_key,
            source_evidence_id=source["id"],
            asset_path=asset_path,
            prompt=prompt,
            result=result,
            new_evidence_ids=new_ids,
            resolved=resolved,
        )
