from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .change import ChangeSignal
from .frame_delta import FrameDeltaDetector
from .models import Evidence, Modality, ReadingMode
from .sources import (
    ForegroundWindowSnapshot,
    ForegroundWindowSource,
    ScreenFrame,
    ScreenSource,
    UIAutomationSnapshot,
    UIAutomationSource,
)
from .world_state import WorldState


@dataclass(frozen=True)
class StreamEvent:
    kind: str
    target: str
    significance: float
    value: Any
    previous: Any = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def suggested_mode(self) -> ReadingMode:
        if self.significance < 0.10:
            return ReadingMode.MONITOR
        if self.significance < 0.30:
            return ReadingMode.SKIM
        if self.significance < 0.60:
            return ReadingMode.SEARCH
        return ReadingMode.INSPECT


@dataclass
class RealStreamConfig:
    screen_change_threshold: float = 0.03
    screen_goal_relevance: float = 0.35
    foreground_significance: float = 0.55
    uia_significance: float = 0.45
    screen_fact_ttl: float = 2.0
    foreground_fact_ttl: float = 2.0
    uia_fact_ttl: float = 3.0


class RealStreamMonitor:
    """
    Fast-loop desktop monitor.

    It converts raw/structured desktop changes into compact events and volatile
    WorldState facts. It does not invoke a VLM. High-significance events can be
    handed to the slow APR controller for semantic inspection.
    """

    def __init__(
        self,
        world: WorldState,
        *,
        screen_source: Optional[ScreenSource] = None,
        foreground_source: Optional[ForegroundWindowSource] = None,
        uia_source: Optional[UIAutomationSource] = None,
        delta_detector: Optional[FrameDeltaDetector] = None,
        config: Optional[RealStreamConfig] = None,
    ) -> None:
        self.world = world
        self.screen_source = screen_source
        self.foreground_source = foreground_source
        self.uia_source = uia_source
        self.delta_detector = delta_detector or FrameDeltaDetector()
        self.config = config or RealStreamConfig()

        self._last_frame: Optional[ScreenFrame] = None
        self._last_foreground: Optional[ForegroundWindowSnapshot] = None
        self._last_uia: Optional[UIAutomationSnapshot] = None

        self._configure_schema()

    @property
    def latest_frame(self) -> Optional[ScreenFrame]:
        return self._last_frame

    def _configure_schema(self) -> None:
        for key in (
            "desktop.screen.changed",
            "desktop.screen.change_ratio",
            "desktop.screen.delta_mean",
            "desktop.screen.change_bbox",
        ):
            self.world.configure_fact(
                key,
                ttl=self.config.screen_fact_ttl,
                volatile=True,
            )

        for key in (
            "desktop.foreground.title",
            "desktop.foreground.hwnd",
            "desktop.foreground.pid",
        ):
            self.world.configure_fact(
                key,
                ttl=self.config.foreground_fact_ttl,
                volatile=True,
            )

        for key in (
            "desktop.uia.digest",
            "desktop.uia.element_count",
        ):
            self.world.configure_fact(
                key,
                ttl=self.config.uia_fact_ttl,
                volatile=True,
            )

    def _write(
        self,
        key: str,
        value: Any,
        *,
        source: str,
        confidence: float = 0.99,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.world.revise(
            Evidence(
                claim_key=key,
                observed_value=value,
                modality=(Modality.VISION if source == "screen_delta" else Modality.STRUCTURED),
                source=source,
                confidence=confidence,
                cost=0.0,
                metadata=metadata or {},
            )
        )

    def _poll_screen(self) -> List[StreamEvent]:
        if self.screen_source is None:
            return []

        frame = self.screen_source.capture()
        if self._last_frame is None:
            self._last_frame = frame
            self._write("desktop.screen.changed", False, source="screen_delta")
            self._write("desktop.screen.change_ratio", 0.0, source="screen_delta")
            self._write("desktop.screen.delta_mean", 0.0, source="screen_delta")
            self._write("desktop.screen.change_bbox", None, source="screen_delta")
            return []

        delta = self.delta_detector.compare(self._last_frame, frame)
        self._last_frame = frame

        changed = delta.changed_ratio >= self.config.screen_change_threshold
        self._write(
            "desktop.screen.changed",
            changed,
            source="screen_delta",
            metadata={"magnitude": delta.magnitude},
        )
        self._write(
            "desktop.screen.change_ratio",
            round(delta.changed_ratio, 6),
            source="screen_delta",
        )
        self._write(
            "desktop.screen.delta_mean",
            round(delta.mean_abs_delta, 6),
            source="screen_delta",
        )
        self._write(
            "desktop.screen.change_bbox",
            delta.bbox,
            source="screen_delta",
        )

        if not changed:
            return []

        signal = ChangeSignal(
            magnitude=delta.magnitude,
            novelty=min(1.0, delta.changed_ratio * 2.0),
            goal_relevance=self.config.screen_goal_relevance,
        )
        return [
            StreamEvent(
                kind="screen_change",
                target="desktop.screen",
                significance=signal.significance(),
                value=delta.changed_ratio,
                metadata={
                    "mean_abs_delta": delta.mean_abs_delta,
                    "bbox": delta.bbox,
                    "sampled_pixels": delta.sampled_pixels,
                },
            )
        ]

    def _poll_foreground(self) -> List[StreamEvent]:
        if self.foreground_source is None:
            return []

        snap = self.foreground_source.snapshot()
        previous = self._last_foreground
        self._last_foreground = snap

        self._write(
            "desktop.foreground.title",
            snap.title,
            source="win32_foreground",
            metadata={"hwnd": snap.hwnd, "pid": snap.pid},
        )
        self._write("desktop.foreground.hwnd", snap.hwnd, source="win32_foreground")
        self._write("desktop.foreground.pid", snap.pid, source="win32_foreground")

        if previous is None:
            return []

        if (snap.hwnd, snap.title, snap.pid) == (
            previous.hwnd,
            previous.title,
            previous.pid,
        ):
            return []

        return [
            StreamEvent(
                kind="foreground_changed",
                target="desktop.foreground",
                significance=self.config.foreground_significance,
                value={"hwnd": snap.hwnd, "title": snap.title, "pid": snap.pid},
                previous={
                    "hwnd": previous.hwnd,
                    "title": previous.title,
                    "pid": previous.pid,
                },
            )
        ]

    def _poll_uia(self) -> List[StreamEvent]:
        if self.uia_source is None:
            return []

        snap = self.uia_source.snapshot()
        previous = self._last_uia
        self._last_uia = snap

        self._write(
            "desktop.uia.digest",
            snap.digest,
            source="windows_uia",
            metadata={
                "sample": [
                    {"name": e.name, "control_type": e.control_type} for e in snap.elements[:20]
                ]
            },
        )
        self._write(
            "desktop.uia.element_count",
            len(snap.elements),
            source="windows_uia",
        )

        if previous is None or previous.digest == snap.digest:
            return []

        return [
            StreamEvent(
                kind="uia_changed",
                target="desktop.uia",
                significance=self.config.uia_significance,
                value=snap.digest,
                previous=previous.digest,
                metadata={"element_count": len(snap.elements)},
            )
        ]

    def poll_once(self) -> List[StreamEvent]:
        events: List[StreamEvent] = []
        events.extend(self._poll_foreground())
        events.extend(self._poll_uia())
        events.extend(self._poll_screen())
        return sorted(events, key=lambda e: e.significance, reverse=True)

    @staticmethod
    def escalation_candidates(
        events: List[StreamEvent],
        *,
        threshold: float = 0.30,
    ) -> List[StreamEvent]:
        return [e for e in events if e.significance >= threshold]
