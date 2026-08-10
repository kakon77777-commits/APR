from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Dict, Optional

from .models import (
    FactStatus,
    Goal,
    Modality,
    PerceptualAction,
    ReadingMode,
)
from .world_state import WorldState


@dataclass
class ChannelProfile:
    modality: Modality
    reliability: float
    cost: float
    available: bool = True
    directness: float = 0.5

    def __post_init__(self) -> None:
        if not isfinite(self.reliability) or not 0.0 <= self.reliability <= 1.0:
            raise ValueError("reliability must be a finite value between 0 and 1")
        if not isfinite(self.cost) or self.cost < 0.0:
            raise ValueError("cost must be a finite non-negative value")
        if not isfinite(self.directness) or not 0.0 <= self.directness <= 1.0:
            raise ValueError("directness must be a finite value between 0 and 1")


class PolicyController:
    """
    Heuristic policy for architecture validation.
    Replaceable by contextual bandit / RL / learned VOI policy.
    """

    def __init__(self, channel_profiles: Dict[Modality, ChannelProfile]) -> None:
        self.channels = channel_profiles

    def _channel_score(self, profile: ChannelProfile, risk: float, revisit: bool) -> float:
        if not profile.available:
            return -1e9
        # High reliability and directness are valuable; cost is penalized.
        score = (
            1.15 * profile.reliability
            + 0.35 * profile.directness
            + 0.20 * risk
            - 0.08 * profile.cost
        )
        if revisit and profile.modality in (
            Modality.VISION,
            Modality.SENSOR,
            Modality.STRUCTURED,
        ):
            score += 0.12
        return score

    def choose_modality(self, risk: float, revisit: bool = False) -> Optional[ChannelProfile]:
        candidates = [p for p in self.channels.values() if p.available]
        if not candidates:
            return None
        return max(candidates, key=lambda p: self._channel_score(p, risk, revisit))

    def decide(self, world: WorldState, goal: Goal) -> PerceptualAction:
        fact = world.get(goal.required_fact)

        if (
            fact.status == FactStatus.KNOWN
            and fact.confidence >= goal.min_confidence
            and goal.risk < 0.75
        ):
            return PerceptualAction(
                target=goal.required_fact,
                modality=None,
                mode=ReadingMode.NO_OBSERVATION,
                expected_gain=0.0,
                estimated_cost=0.0,
                reason="Existing world-state fact is fresh and sufficiently confident.",
            )

        revisit = fact.status == FactStatus.CONTRADICTED
        channel = self.choose_modality(risk=goal.risk, revisit=revisit)

        if channel is None:
            return PerceptualAction(
                target=goal.required_fact,
                modality=None,
                mode=ReadingMode.EPISTEMIC_ACTION,
                expected_gain=0.4,
                estimated_cost=1.0,
                reason="No direct modality is available; change observation conditions.",
                epistemic_action="acquire_new_view_or_channel",
            )

        if revisit:
            mode = ReadingMode.REVISIT
            expected_gain = 0.9
            reason = "Fact is contradicted; targeted re-observation is required."
        elif fact.status == FactStatus.STALE:
            mode = ReadingMode.INSPECT
            expected_gain = 0.75
            reason = "Fact is stale; refresh the current belief."
        elif fact.status in (FactStatus.UNKNOWN, FactStatus.UNCERTAIN):
            mode = ReadingMode.INSPECT if goal.risk >= 0.5 else ReadingMode.SEARCH
            expected_gain = 0.8 if goal.risk >= 0.5 else 0.6
            reason = "Required fact is unknown/uncertain."
        else:
            # High-risk goals may re-verify a known fact.
            mode = ReadingMode.INSPECT
            expected_gain = 0.55 + 0.35 * goal.risk
            reason = "Risk threshold requests re-verification before action."

        return PerceptualAction(
            target=goal.required_fact,
            modality=channel.modality,
            mode=mode,
            expected_gain=min(1.0, expected_gain),
            estimated_cost=channel.cost,
            reason=reason,
        )
