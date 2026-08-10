import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apr_runtime import EventLedger, NativeEvent


class EventLedgerTests(unittest.TestCase):
    def test_append_query_and_compact(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventLedger(Path(tmp) / "events.sqlite3")
            old_low = NativeEvent("low", "test", "x", 0.2, timestamp=time.time() - 1000)
            old_high = NativeEvent("high", "test", "x", 0.9, timestamp=time.time() - 1000)
            new_low = NativeEvent("low", "test", "y", 0.2)
            for e in (old_low, old_high, new_low):
                ledger.append(e)
            self.assertEqual(ledger.count(), 3)
            self.assertEqual(len(ledger.recent(min_significance=0.5)), 1)
            self.assertEqual(
                ledger.compact(older_than=time.time() - 100, keep_significance_at_least=0.75),
                1,
            )
            self.assertEqual(ledger.count(), 2)


if __name__ == "__main__":
    unittest.main()
