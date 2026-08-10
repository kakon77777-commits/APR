from __future__ import annotations

from .browser import BrowserSource
from .models import Evidence, Modality, PerceptualAction


class BrowserStructuredAdapter:
    modality = Modality.STRUCTURED

    def __init__(
        self,
        source: BrowserSource,
        *,
        reliability: float = 0.995,
        base_cost: float = 0.4,
    ) -> None:
        self.source = source
        self.reliability = reliability
        self.base_cost = base_cost

    def configure_world(self, world) -> None:
        for key in (
            "browser.url",
            "browser.title",
            "browser.aria.snapshot",
            "browser.aria.digest",
            "browser.dom.digest",
            "browser.dom.element_count",
            "browser.active_element",
        ):
            world.configure_fact(key, ttl=2.0, volatile=True)

    def observe(self, action: PerceptualAction) -> Evidence:
        snap = self.source.snapshot()

        values = {
            "browser.url": snap.url,
            "browser.title": snap.title,
            "browser.aria.snapshot": snap.aria_snapshot,
            "browser.aria.digest": snap.aria_digest,
            "browser.dom.digest": snap.dom_digest,
            "browser.dom.element_count": snap.dom_element_count,
            "browser.active_element": snap.active_element,
        }
        if action.target not in values:
            raise KeyError(f"Unsupported browser fact: {action.target}")

        confidence = self.reliability
        if action.target in ("browser.aria.snapshot", "browser.dom.digest"):
            confidence = max(0.0, confidence - 0.01)

        return Evidence(
            claim_key=action.target,
            observed_value=values[action.target],
            modality=Modality.STRUCTURED,
            source="browser_native_state",
            confidence=confidence,
            cost=action.estimated_cost,
            metadata={
                "url": snap.url,
                "title": snap.title,
                "dom_element_count": snap.dom_element_count,
            },
        )
