from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .archive import EvidenceArchive
from .image_ops import crop_frame, frame_to_png_bytes, pad_bbox
from .models import Evidence, Modality
from .semantic import SemanticInspector, SemanticResult
from .sources import ScreenFrame
from .stream import StreamEvent
from .world_state import WorldState


@dataclass
class SemanticPipelineConfig:
    roi_padding: int = 28
    summary_key: str = "desktop.screen.semantic_summary"
    summary_ttl: float = 15.0
    min_fact_confidence: float = 0.35


@dataclass
class SemanticInspectionRecord:
    event: StreamEvent
    crop_path: Path
    prompt: str
    result: SemanticResult
    evidence_ids: List[str]


class SemanticEvidencePipeline:
    """
    Upgrade low-level screen change into semantic Evidence Contracts.

    The pipeline archives the exact ROI image used by the semantic inspector,
    preserving provenance so future REVISIT can read the same evidence again.
    """

    def __init__(
        self,
        world: WorldState,
        archive: EvidenceArchive,
        inspector: SemanticInspector,
        *,
        config: Optional[SemanticPipelineConfig] = None,
    ) -> None:
        self.world = world
        self.archive = archive
        self.inspector = inspector
        self.config = config or SemanticPipelineConfig()

        self.world.configure_fact(
            self.config.summary_key,
            ttl=self.config.summary_ttl,
            volatile=True,
        )

    def _prompt_for(
        self,
        event: StreamEvent,
        goal: Optional[str],
    ) -> str:
        goal_text = goal or "Maintain an accurate desktop world state."
        return (
            "Inspect only this changed desktop ROI. "
            "Identify the most decision-relevant semantic change and emit "
            "structured facts when justified. Do not invent details outside "
            "the visible ROI. "
            f"Current goal: {goal_text} "
            f"Low-level event: {event.kind}; significance={event.significance:.3f}."
        )

    def inspect_screen_event(
        self,
        event: StreamEvent,
        frame: ScreenFrame,
        *,
        goal: Optional[str] = None,
    ) -> SemanticInspectionRecord:
        bbox = event.metadata.get("bbox")
        if not bbox:
            bbox = (0, 0, frame.width, frame.height)

        bbox = pad_bbox(
            tuple(bbox),
            frame.width,
            frame.height,
            padding=self.config.roi_padding,
        )
        crop = crop_frame(frame, bbox)
        png = frame_to_png_bytes(crop)
        crop_path = self.archive.store_asset(
            png,
            extension=".png",
            prefix="screen-roi",
        )

        prompt = self._prompt_for(event, goal)
        context = {
            "event_kind": event.kind,
            "event_target": event.target,
            "event_significance": event.significance,
            "bbox": bbox,
            "frame_timestamp": frame.timestamp,
            "frame_origin": [frame.left, frame.top],
            "goal": goal,
        }

        result = self.inspector.inspect(
            crop_path,
            prompt=prompt,
            context=context,
        )

        evidence_ids: List[str] = []

        # Always preserve a compact semantic summary as a volatile state.
        summary_ev = Evidence(
            claim_key=self.config.summary_key,
            observed_value=result.summary,
            modality=Modality.VISION,
            source=self.inspector.name,
            confidence=max(0.0, min(1.0, result.confidence)),
            cost=float(self.inspector.estimated_cost),
            pointer=str(crop_path),
            metadata={
                "semantic": True,
                "bbox": bbox,
                "event_kind": event.kind,
                "event_significance": event.significance,
            },
        )
        self.world.revise(summary_ev)
        self.archive.record(summary_ev, asset_path=crop_path)
        evidence_ids.append(summary_ev.id)

        for fact in result.facts:
            if fact.confidence < self.config.min_fact_confidence:
                continue

            self.world.configure_fact(
                fact.key,
                ttl=fact.ttl,
                volatile=fact.volatile,
            )
            ev = Evidence(
                claim_key=fact.key,
                observed_value=fact.value,
                modality=Modality.VISION,
                source=self.inspector.name,
                confidence=max(0.0, min(1.0, fact.confidence)),
                cost=float(self.inspector.estimated_cost),
                pointer=str(crop_path),
                metadata={
                    **fact.metadata,
                    "semantic": True,
                    "bbox": bbox,
                    "event_kind": event.kind,
                    "summary": result.summary,
                },
            )
            current = self.world.get(fact.key)
            if current.status.value == "contradicted":
                self.world.resolve_conflict(fact.key, ev)
            else:
                self.world.revise(ev)
            self.archive.record(ev, asset_path=crop_path)
            evidence_ids.append(ev.id)

        return SemanticInspectionRecord(
            event=event,
            crop_path=crop_path,
            prompt=prompt,
            result=result,
            evidence_ids=evidence_ids,
        )
