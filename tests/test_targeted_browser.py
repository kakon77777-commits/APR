import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apr_runtime import NativeEvent, TargetedBrowserReader


class FakeSession:
    def __init__(self):
        self.calls = []

    def send(self, method, **params):
        self.calls.append((method, params))
        if method == "DOM.describeNode":
            return {"node": {"nodeId": params.get("nodeId"), "nodeName": "BUTTON"}}
        if method == "DOM.getOuterHTML":
            return {"outerHTML": "<button>OK</button>"}
        if method == "Accessibility.getPartialAXTree":
            return {"nodes": [{"role": {"value": "button"}, "name": {"value": "OK"}}]}
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1, "nodeName": "#document"}}
        raise AssertionError(method)


class FakeEvents:
    def __init__(self, generation=1):
        self.generation = generation
        self.session = FakeSession()

    def reseed_document(self):
        return self.session.send("DOM.getDocument", depth=2, pierce=True)


class TargetedBrowserReaderTests(unittest.TestCase):
    def test_targeted_node_reads_dom_html_and_ax(self):
        events = FakeEvents(3)
        reader = TargetedBrowserReader(events, depth=1)
        ev = NativeEvent(
            "DOM.attributeModified",
            "browser_cdp",
            "browser.dom.node:42",
            0.35,
            node_id=42,
            payload={"document_generation": 3},
        )
        result = reader.read_event(ev)
        self.assertFalse(result.refreshed_document)
        self.assertEqual(result.dom["nodeName"], "BUTTON")
        self.assertEqual(result.outer_html, "<button>OK</button>")
        self.assertEqual(result.accessibility_nodes[0]["role"]["value"], "button")

    def test_document_update_reseeds(self):
        events = FakeEvents(4)
        reader = TargetedBrowserReader(events)
        ev = NativeEvent(
            "DOM.documentUpdated",
            "browser_cdp",
            "browser.document",
            0.9,
            payload={"document_generation": 4},
        )
        result = reader.read_event(ev)
        self.assertTrue(result.refreshed_document)
        self.assertEqual(result.dom["nodeName"], "#document")


if __name__ == "__main__":
    unittest.main()
