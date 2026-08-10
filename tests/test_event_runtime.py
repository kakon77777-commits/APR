import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apr_runtime import (
    EventLedger,
    EventNativeRuntime,
    EvidenceStore,
    NativeEvent,
    WorldState,
)


class EventNativeRuntimeTests(unittest.TestCase):
    def test_event_is_not_world_state_until_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            world = WorldState(EvidenceStore())
            ledger = EventLedger(Path(tmp) / "events.sqlite3")
            rt = EventNativeRuntime(world, ledger)
            ev = NativeEvent(
                "DOM.attributeModified",
                "browser_cdp",
                "browser.dom.node:42",
                0.4,
                node_id=42,
            )
            rt.record(ev)
            self.assertEqual(ledger.count(), 1)
            self.assertEqual(world.snapshot(), {})
            evidence = rt.write_verified_state(
                ev,
                key="browser.dialog.expanded",
                value=True,
                confidence=0.98,
                source="targeted_dom_read",
            )
            self.assertTrue(world.get("browser.dialog.expanded").value)
            self.assertEqual(evidence.metadata["native_event_id"], ev.id)


if __name__ == "__main__":
    unittest.main()
