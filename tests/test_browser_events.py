import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apr_runtime import BrowserCDPEventSource, BrowserEventConfig, EventLedger


class FakeSession:
    def __init__(self):
        self.handlers = {}
        self.calls = []
        self.detached = False

    def send(self, method, **params):
        self.calls.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1}}
        return {}

    def on(self, method, handler):
        self.handlers[method] = handler

    def detach(self):
        self.detached = True

    def emit(self, method, params=None):
        self.handlers[method](params or {})


class FakeContext:
    def __init__(self, session):
        self.session = session

    def new_cdp_session(self, page):
        return self.session


class FakePage:
    def __init__(self, session):
        self.context = FakeContext(session)


class FakeBrowser:
    def __init__(self):
        self.session = FakeSession()
        self._page = FakePage(self.session)

    def page(self):
        return self._page


class BrowserCDPEventSourceTests(unittest.TestCase):
    def test_start_seeds_document_and_records_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            browser = FakeBrowser()
            ledger = EventLedger(Path(tmp) / "events.sqlite3")
            source = BrowserCDPEventSource(
                browser, ledger=ledger, config=BrowserEventConfig(seed_depth=2)
            )
            source.start()
            methods = [m for m, _ in browser.session.calls]
            self.assertIn("DOM.enable", methods)
            self.assertIn("DOM.getDocument", methods)
            browser.session.emit(
                "DOM.attributeModified",
                {"nodeId": 42, "name": "aria-expanded", "value": "true"},
            )
            events = source.drain()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].node_id, 42)
            self.assertEqual(ledger.count(), 1)
            source.close()
            self.assertTrue(browser.session.detached)

    def test_document_updated_increments_generation(self):
        browser = FakeBrowser()
        source = BrowserCDPEventSource(browser)
        source.start()
        self.assertEqual(source.generation, 0)
        browser.session.emit("DOM.documentUpdated", {})
        events = source.drain()
        self.assertEqual(source.generation, 1)
        self.assertEqual(events[0].payload["document_generation"], 1)
        self.assertEqual(events[0].target, "browser.document")


if __name__ == "__main__":
    unittest.main()
