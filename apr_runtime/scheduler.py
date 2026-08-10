from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional

from .event_ledger import EventLedger, NativeEvent
from .stream import StreamEvent


@dataclass
class SchedulerConfig:
    max_queue: int = 512
    coalesce_window: float = 0.20
    duplicate_window: float = 0.10
    critical_significance: float = 0.85
    admission_margin: float = 0.05
    aging_rate: float = 0.015
    max_age_boost: float = 0.25
    default_source_weight: float = 1.0
    source_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "browser_cdp": 1.00,
            "win32_winevent": 1.00,
            "screen_delta": 0.85,
            "windows_uia": 0.90,
            "browser_native_state": 0.95,
            "semantic": 1.10,
            "periodic_refresh": 0.70,
        }
    )


@dataclass
class SchedulerMetrics:
    ingested: int = 0
    queued: int = 0
    coalesced: int = 0
    duplicates: int = 0
    dropped: int = 0
    evicted: int = 0
    dispatched: int = 0
    refresh_emitted: int = 0


@dataclass
class ScheduledEvent:
    event: NativeEvent
    key: str
    base_priority: float
    first_enqueued: float
    last_updated: float
    coalesced_count: int = 1
    duplicate_count: int = 0
    source_event_ids: List[str] = field(default_factory=list)

    def effective_priority(self, now: float, config: SchedulerConfig) -> float:
        age = max(0.0, now - self.first_enqueued)
        age_boost = min(config.max_age_boost, age * config.aging_rate)
        return self.base_priority + age_boost


@dataclass
class RefreshSpec:
    name: str
    target: str
    interval: float
    significance: float = 0.25
    source: str = "periodic_refresh"
    payload: Dict[str, Any] = field(default_factory=dict)
    next_due: Optional[float] = None


class UnifiedEventScheduler:
    """Bounded, coalescing, priority-aware scheduler for APR event streams."""

    def __init__(
        self,
        *,
        config: Optional[SchedulerConfig] = None,
        ledger: Optional[EventLedger] = None,
    ) -> None:
        self.config = config or SchedulerConfig()
        if self.config.max_queue < 1:
            raise ValueError("max_queue must be >= 1")
        self.ledger = ledger
        self.metrics = SchedulerMetrics()
        self._pending: Dict[str, ScheduledEvent] = {}
        self._last_fingerprint_at: Dict[str, float] = {}
        self._refresh: Dict[str, RefreshSpec] = {}

    @staticmethod
    def _stable_payload(payload: Dict[str, Any]) -> str:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    def fingerprint(self, event: NativeEvent) -> str:
        raw = "|".join(
            [
                event.source,
                event.kind,
                event.target,
                str(event.node_id),
                str(event.backend_node_id),
                str(event.hwnd),
                self._stable_payload(event.payload),
            ]
        ).encode("utf-8", "replace")
        return sha256(raw).hexdigest()

    @staticmethod
    def coalesce_key(event: NativeEvent) -> str:
        identity = (
            event.backend_node_id
            if event.backend_node_id is not None
            else event.node_id
            if event.node_id is not None
            else event.hwnd
            if event.hwnd is not None
            else ""
        )
        return f"{event.source}|{event.kind}|{event.target}|{identity}"

    def _base_priority(self, event: NativeEvent) -> float:
        weight = self.config.source_weights.get(event.source, self.config.default_source_weight)
        return max(0.0, min(1.5, float(event.significance) * float(weight)))

    def _persist(self, event: NativeEvent) -> None:
        if self.ledger is not None:
            self.ledger.append(event)

    def _merge(
        self,
        current: ScheduledEvent,
        event: NativeEvent,
        now: float,
        *,
        duplicate: bool,
    ) -> ScheduledEvent:
        payload = dict(current.event.payload)
        payload.update(event.payload)
        payload["scheduler_coalesced_count"] = current.coalesced_count + 1
        payload["scheduler_duplicate_count"] = current.duplicate_count + (1 if duplicate else 0)

        merged_event = NativeEvent(
            kind=event.kind,
            source=event.source,
            target=event.target,
            significance=max(current.event.significance, event.significance),
            timestamp=max(current.event.timestamp, event.timestamp),
            node_id=event.node_id if event.node_id is not None else current.event.node_id,
            backend_node_id=(
                event.backend_node_id
                if event.backend_node_id is not None
                else current.event.backend_node_id
            ),
            hwnd=event.hwnd if event.hwnd is not None else current.event.hwnd,
            payload=payload,
        )
        return ScheduledEvent(
            event=merged_event,
            key=current.key,
            base_priority=max(current.base_priority, self._base_priority(event)),
            first_enqueued=current.first_enqueued,
            last_updated=now,
            coalesced_count=current.coalesced_count + 1,
            duplicate_count=current.duplicate_count + (1 if duplicate else 0),
            source_event_ids=current.source_event_ids + [event.id],
        )

    def _lowest_pending(self, now: float) -> Optional[ScheduledEvent]:
        if not self._pending:
            return None
        return min(
            self._pending.values(),
            key=lambda item: item.effective_priority(now, self.config),
        )

    def ingest(
        self, event: NativeEvent, *, now: Optional[float] = None, persist: bool = True
    ) -> bool:
        now = time.time() if now is None else float(now)
        self.metrics.ingested += 1
        if persist:
            self._persist(event)

        key = self.coalesce_key(event)
        fingerprint = self.fingerprint(event)
        last_fp = self._last_fingerprint_at.get(fingerprint)
        is_duplicate = last_fp is not None and now - last_fp <= self.config.duplicate_window
        self._last_fingerprint_at[fingerprint] = now

        current = self._pending.get(key)
        if current is not None and now - current.last_updated <= self.config.coalesce_window:
            self._pending[key] = self._merge(current, event, now, duplicate=is_duplicate)
            self.metrics.coalesced += 1
            if is_duplicate:
                self.metrics.duplicates += 1
            return True

        if len(self._pending) >= self.config.max_queue:
            lowest = self._lowest_pending(now)
            incoming = self._base_priority(event)
            critical = event.significance >= self.config.critical_significance
            if lowest is None:
                self.metrics.dropped += 1
                return False
            lowest_priority = lowest.effective_priority(now, self.config)
            if critical or incoming >= lowest_priority + self.config.admission_margin:
                self._pending.pop(lowest.key, None)
                self.metrics.evicted += 1
            else:
                self.metrics.dropped += 1
                return False

        self._pending[key] = ScheduledEvent(
            event=event,
            key=key,
            base_priority=self._base_priority(event),
            first_enqueued=now,
            last_updated=now,
            source_event_ids=[event.id],
        )
        self.metrics.queued += 1
        if is_duplicate:
            self.metrics.duplicates += 1
        return True

    def ingest_many(
        self,
        events: Iterable[NativeEvent],
        *,
        now: Optional[float] = None,
        persist: bool = True,
    ) -> int:
        accepted = 0
        base_now = time.time() if now is None else float(now)
        for index, event in enumerate(events):
            if self.ingest(event, now=base_now + index * 1e-9, persist=persist):
                accepted += 1
        return accepted

    @staticmethod
    def from_stream(event: StreamEvent, *, source: str = "stream") -> NativeEvent:
        payload = {
            "value": event.value,
            "previous": event.previous,
            **dict(event.metadata),
        }
        return NativeEvent(
            kind=event.kind,
            source=source,
            target=event.target,
            significance=event.significance,
            timestamp=event.timestamp,
            payload=payload,
        )

    def ingest_stream(
        self,
        event: StreamEvent,
        *,
        source: str = "stream",
        now: Optional[float] = None,
        persist: bool = True,
    ) -> bool:
        return self.ingest(self.from_stream(event, source=source), now=now, persist=persist)

    def pop_batch(
        self, *, max_items: int = 16, now: Optional[float] = None
    ) -> List[ScheduledEvent]:
        now = time.time() if now is None else float(now)
        if max_items < 1:
            return []
        ordered = sorted(
            self._pending.values(),
            key=lambda item: (
                item.effective_priority(now, self.config),
                item.event.significance,
                -item.first_enqueued,
            ),
            reverse=True,
        )[:max_items]
        for item in ordered:
            self._pending.pop(item.key, None)
        self.metrics.dispatched += len(ordered)
        return ordered

    def pending(self, *, now: Optional[float] = None) -> List[ScheduledEvent]:
        now = time.time() if now is None else float(now)
        return sorted(
            self._pending.values(),
            key=lambda item: item.effective_priority(now, self.config),
            reverse=True,
        )

    def pending_count(self) -> int:
        return len(self._pending)

    def register_refresh(self, spec: RefreshSpec, *, now: Optional[float] = None) -> None:
        now = time.time() if now is None else float(now)
        if spec.interval <= 0:
            raise ValueError("refresh interval must be > 0")
        if spec.next_due is None:
            spec.next_due = now + spec.interval
        self._refresh[spec.name] = spec

    def emit_due_refreshes(self, *, now: Optional[float] = None) -> List[NativeEvent]:
        now = time.time() if now is None else float(now)
        emitted: List[NativeEvent] = []
        for spec in self._refresh.values():
            if spec.next_due is None:
                spec.next_due = now + spec.interval
                continue
            if now < spec.next_due:
                continue
            event = NativeEvent(
                kind="apr.periodic_refresh",
                source=spec.source,
                target=spec.target,
                significance=spec.significance,
                timestamp=now,
                payload={"refresh_name": spec.name, **dict(spec.payload)},
            )
            self.ingest(event, now=now, persist=True)
            emitted.append(event)
            self.metrics.refresh_emitted += 1
            spec.next_due = now + spec.interval
        return emitted
