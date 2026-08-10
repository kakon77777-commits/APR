import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    EventLedger,
    NativeEvent,
    RefreshSpec,
    SchedulerConfig,
    UnifiedEventScheduler,
)


def ev(
    kind="DOM.characterDataModified",
    target="node:1",
    sig=0.4,
    source="browser_cdp",
    payload=None,
):
    return NativeEvent(
        kind=kind, source=source, target=target, significance=sig, payload=payload or {}
    )


class SchedulerTests(unittest.TestCase):
    def test_burst_coalesces_same_target(self):
        s = UnifiedEventScheduler(config=SchedulerConfig(coalesce_window=1.0))
        for i in range(30):
            s.ingest(ev(payload={"text": str(i)}), now=100 + i * 0.01, persist=False)
        self.assertEqual(s.pending_count(), 1)
        item = s.pending(now=101)[0]
        self.assertEqual(item.coalesced_count, 30)
        self.assertEqual(item.event.payload["text"], "29")
        self.assertEqual(s.metrics.coalesced, 29)

    def test_duplicate_is_counted(self):
        s = UnifiedEventScheduler(config=SchedulerConfig(coalesce_window=1.0, duplicate_window=1.0))
        a = ev(payload={"x": 1})
        b = ev(payload={"x": 1})
        s.ingest(a, now=1.0, persist=False)
        s.ingest(b, now=1.1, persist=False)
        self.assertEqual(s.pending()[0].duplicate_count, 1)
        self.assertEqual(s.metrics.duplicates, 1)

    def test_backpressure_admits_critical_and_evicts_low(self):
        s = UnifiedEventScheduler(config=SchedulerConfig(max_queue=2))
        s.ingest(ev(target="low1", sig=0.10), now=1, persist=False)
        s.ingest(ev(target="low2", sig=0.20), now=2, persist=False)
        accepted = s.ingest(ev(target="critical", sig=0.95), now=3, persist=False)
        self.assertTrue(accepted)
        targets = {x.event.target for x in s.pending(now=3)}
        self.assertIn("critical", targets)
        self.assertEqual(len(targets), 2)
        self.assertEqual(s.metrics.evicted, 1)

    def test_backpressure_drops_low_value_new_event(self):
        s = UnifiedEventScheduler(config=SchedulerConfig(max_queue=1))
        s.ingest(ev(target="high", sig=0.80), now=1, persist=False)
        accepted = s.ingest(ev(target="low", sig=0.10), now=2, persist=False)
        self.assertFalse(accepted)
        self.assertEqual(s.metrics.dropped, 1)
        self.assertEqual(s.pending()[0].event.target, "high")

    def test_age_boost_prevents_permanent_starvation(self):
        s = UnifiedEventScheduler(config=SchedulerConfig(aging_rate=0.20, max_age_boost=0.50))
        s.ingest(ev(target="old", sig=0.30), now=0, persist=False)
        s.ingest(ev(target="new", sig=0.50), now=10, persist=False)
        batch = s.pop_batch(max_items=1, now=10)
        self.assertEqual(batch[0].event.target, "old")

    def test_periodic_refresh_is_scheduled(self):
        s = UnifiedEventScheduler()
        s.register_refresh(
            RefreshSpec("browser", "browser.page", interval=10, significance=0.3),
            now=100,
        )
        self.assertEqual(s.emit_due_refreshes(now=109), [])
        emitted = s.emit_due_refreshes(now=110)
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].kind, "apr.periodic_refresh")
        self.assertEqual(s.pending_count(), 1)

    def test_scheduler_can_persist_to_event_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventLedger(Path(tmp) / "events.sqlite3")
            s = UnifiedEventScheduler(ledger=ledger)
            s.ingest(ev(), persist=True)
            self.assertEqual(ledger.count(), 1)


if __name__ == "__main__":
    unittest.main()
