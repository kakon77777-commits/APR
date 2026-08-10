import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import StreamEvent, UnifiedEventRuntime, UnifiedEventScheduler


class OrchestratorTests(unittest.TestCase):
    def test_stream_events_are_normalized_into_one_scheduler(self):
        scheduler = UnifiedEventScheduler()
        runtime = UnifiedEventRuntime(scheduler)
        report = runtime.submit_stream(
            [
                StreamEvent("screen_change", "desktop.screen", 0.4, 0.2),
                StreamEvent("screen_change", "desktop.screen", 0.5, 0.3),
            ],
            source="screen_delta",
            now=1,
            persist=False,
        )
        self.assertEqual(report.accepted, 2)
        self.assertEqual(scheduler.pending_count(), 1)
        item = scheduler.pending()[0]
        self.assertEqual(item.coalesced_count, 2)
        self.assertEqual(item.event.source, "screen_delta")


if __name__ == "__main__":
    unittest.main()
