from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChangeSignal:
    magnitude: float = 0.0
    novelty: float = 0.0
    goal_relevance: float = 0.0
    uncertainty: float = 0.0
    risk: float = 0.0
    conflict: float = 0.0

    def significance(self) -> float:
        # Intentionally not proportional to raw change magnitude.
        score = (
            0.10 * self.magnitude
            + 0.20 * self.novelty
            + 0.25 * self.goal_relevance
            + 0.15 * self.uncertainty
            + 0.20 * self.risk
            + 0.10 * self.conflict
        )
        return max(0.0, min(1.0, score))
