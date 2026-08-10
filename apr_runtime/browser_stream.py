from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .browser import BrowserSnapshot, BrowserSource
from .models import Evidence, Modality
from .stream import StreamEvent
from .world_state import WorldState


@dataclass
class BrowserStreamConfig:
    fact_ttl: float = 2.0
    navigation_significance: float = 0.75
    aria_significance: float = 0.50
    dom_significance: float = 0.45
    focus_significance: float = 0.25


class BrowserStreamMonitor:
    """
    Structured/native browser Fast Loop.

    It turns bounded browser state changes into compact APR StreamEvents.
    """

    def __init__(
        self,
        world: WorldState,
        source: BrowserSource,
        *,
        config: Optional[BrowserStreamConfig] = None,
    ) -> None:
        self.world = world
        self.source = source
        self.config = config or BrowserStreamConfig()
        self._last: Optional[BrowserSnapshot] = None

        for key in (
            "browser.url",
            "browser.title",
            "browser.aria.digest",
            "browser.dom.digest",
            "browser.dom.element_count",
            "browser.active_element",
        ):
            self.world.configure_fact(
                key,
                ttl=self.config.fact_ttl,
                volatile=True,
            )

    def _write(self, key, value, metadata=None):
        self.world.revise(
            Evidence(
                claim_key=key,
                observed_value=value,
                modality=Modality.STRUCTURED,
                source="browser_native_state",
                confidence=0.99,
                cost=0.0,
                metadata=metadata or {},
            )
        )

    def poll_once(self) -> List[StreamEvent]:
        snap = self.source.snapshot()
        prev = self._last
        self._last = snap

        self._write("browser.url", snap.url)
        self._write("browser.title", snap.title)
        self._write("browser.aria.digest", snap.aria_digest)
        self._write("browser.dom.digest", snap.dom_digest)
        self._write("browser.dom.element_count", snap.dom_element_count)
        self._write("browser.active_element", snap.active_element)

        if prev is None:
            return []

        events: List[StreamEvent] = []

        if (prev.url, prev.title) != (snap.url, snap.title):
            events.append(
                StreamEvent(
                    kind="browser_navigation",
                    target="browser.page",
                    significance=self.config.navigation_significance,
                    value={"url": snap.url, "title": snap.title},
                    previous={"url": prev.url, "title": prev.title},
                )
            )

        if prev.aria_digest != snap.aria_digest:
            events.append(
                StreamEvent(
                    kind="browser_aria_changed",
                    target="browser.aria",
                    significance=self.config.aria_significance,
                    value=snap.aria_digest,
                    previous=prev.aria_digest,
                    metadata={"element_count": snap.dom_element_count},
                )
            )

        if prev.dom_digest != snap.dom_digest:
            events.append(
                StreamEvent(
                    kind="browser_dom_changed",
                    target="browser.dom",
                    significance=self.config.dom_significance,
                    value=snap.dom_digest,
                    previous=prev.dom_digest,
                    metadata={"element_count": snap.dom_element_count},
                )
            )

        if prev.active_element != snap.active_element:
            events.append(
                StreamEvent(
                    kind="browser_focus_changed",
                    target="browser.active_element",
                    significance=self.config.focus_significance,
                    value=snap.active_element,
                    previous=prev.active_element,
                )
            )

        return sorted(events, key=lambda e: e.significance, reverse=True)
