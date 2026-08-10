from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Dict, Optional

from .models import Evidence, Modality, PerceptualAction


@dataclass
class ObservationSpec:
    value: Any
    confidence: float = 0.95
    pointer: Optional[str] = None
    metadata: Optional[dict] = None

    def __post_init__(self) -> None:
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be a finite value between 0 and 1")


class BaseAdapter:
    modality: Modality
    reliability: float
    base_cost: float

    def observe(self, action: PerceptualAction) -> Evidence:
        raise NotImplementedError


class SimulatorAdapter(BaseAdapter):
    """
    Deterministic fake perception backend.
    It lets the runtime control layer be tested without pretending a fake VLM
    is meaningful evidence about visual intelligence.
    """

    def __init__(
        self,
        modality: Modality,
        source: str,
        world: Dict[str, ObservationSpec],
        reliability: float,
        base_cost: float,
    ) -> None:
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source must be a non-empty string")
        if not isfinite(reliability) or not 0.0 <= reliability <= 1.0:
            raise ValueError("reliability must be a finite value between 0 and 1")
        if not isfinite(base_cost) or base_cost < 0.0:
            raise ValueError("base_cost must be a finite non-negative value")
        self.modality = modality
        self.source = source
        self.world = world
        self.reliability = reliability
        self.base_cost = base_cost

    def set_observation(self, key: str, spec: ObservationSpec) -> None:
        self.world[key] = spec

    def observe(self, action: PerceptualAction) -> Evidence:
        if action.target not in self.world:
            return Evidence(
                claim_key=action.target,
                observed_value=None,
                modality=self.modality,
                source=self.source,
                confidence=0.0,
                cost=action.estimated_cost,
                metadata={"missing": True},
            )

        spec = self.world[action.target]
        confidence = max(0.0, min(1.0, spec.confidence * self.reliability))
        return Evidence(
            claim_key=action.target,
            observed_value=spec.value,
            modality=self.modality,
            source=self.source,
            confidence=confidence,
            cost=action.estimated_cost,
            pointer=spec.pointer,
            metadata=dict(spec.metadata or {}),
        )
