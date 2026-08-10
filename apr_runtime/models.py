from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any, Dict, List, Optional


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_probability(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a finite value between 0 and 1")


def _require_non_negative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be a finite non-negative value")


class Modality(str, Enum):
    TEXT = "text"
    VISION = "vision"
    VIDEO = "video"
    AUDIO = "audio"
    STRUCTURED = "structured"
    SENSOR = "sensor"


class ReadingMode(str, Enum):
    NO_OBSERVATION = "no_observation"
    MONITOR = "monitor"
    SKIM = "skim"
    SEARCH = "search"
    TRACK = "track"
    INSPECT = "inspect"
    DEEP = "deep"
    REVISIT = "revisit"
    EPISTEMIC_ACTION = "epistemic_action"


class FactStatus(str, Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    UNCERTAIN = "uncertain"
    STALE = "stale"
    CONTRADICTED = "contradicted"


@dataclass
class Evidence:
    claim_key: str
    observed_value: Any
    modality: Modality
    source: str
    confidence: float
    cost: float
    timestamp: float = field(default_factory=time.time)
    pointer: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        _require_non_empty("claim_key", self.claim_key)
        _require_non_empty("source", self.source)
        _require_probability("confidence", self.confidence)
        _require_non_negative("cost", self.cost)
        _require_non_negative("timestamp", self.timestamp)
        _require_non_empty("id", self.id)


@dataclass
class FactState:
    key: str
    value: Any = None
    confidence: float = 0.0
    status: FactStatus = FactStatus.UNKNOWN
    last_verified: float = 0.0
    ttl: float = 60.0
    version: int = 0
    evidence_ids: List[str] = field(default_factory=list)
    volatile: bool = False

    def __post_init__(self) -> None:
        _require_non_empty("key", self.key)
        _require_probability("confidence", self.confidence)
        _require_non_negative("last_verified", self.last_verified)
        _require_non_negative("ttl", self.ttl)
        if self.version < 0:
            raise ValueError("version must be non-negative")

    def age(self, now: Optional[float] = None) -> float:
        now = time.time() if now is None else now
        return float("inf") if self.last_verified <= 0 else max(0.0, now - self.last_verified)

    def refresh_status(self, now: Optional[float] = None) -> FactStatus:
        if self.status == FactStatus.CONTRADICTED:
            return self.status
        if self.value is None:
            self.status = FactStatus.UNKNOWN
        elif self.age(now) > self.ttl:
            self.status = FactStatus.STALE
        elif self.confidence < 0.5:
            self.status = FactStatus.UNCERTAIN
        else:
            self.status = FactStatus.KNOWN
        return self.status


@dataclass
class Budget:
    units: float = 100.0
    spent: float = 0.0

    def __post_init__(self) -> None:
        _require_non_negative("units", self.units)
        _require_non_negative("spent", self.spent)
        if self.spent > self.units:
            raise ValueError("spent must not exceed units")

    @property
    def remaining(self) -> float:
        return max(0.0, self.units - self.spent)

    def can_afford(self, cost: float) -> bool:
        return isfinite(cost) and 0.0 <= cost <= self.remaining

    def spend(self, cost: float) -> None:
        _require_non_negative("cost", cost)
        if not self.can_afford(cost):
            raise RuntimeError(f"Budget exhausted: need {cost:.2f}, remaining {self.remaining:.2f}")
        self.spent += cost


@dataclass
class Goal:
    required_fact: str
    risk: float = 0.2
    min_confidence: float = 0.8
    description: str = ""

    def __post_init__(self) -> None:
        _require_non_empty("required_fact", self.required_fact)
        _require_probability("risk", self.risk)
        _require_probability("min_confidence", self.min_confidence)


@dataclass
class PerceptualAction:
    target: str
    modality: Optional[Modality]
    mode: ReadingMode
    expected_gain: float
    estimated_cost: float
    reason: str
    epistemic_action: Optional[str] = None

    def __post_init__(self) -> None:
        _require_non_empty("target", self.target)
        _require_probability("expected_gain", self.expected_gain)
        _require_non_negative("estimated_cost", self.estimated_cost)
