import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apr_runtime import EventLedger, NativeEvent

with tempfile.TemporaryDirectory() as tmp:
    ledger = EventLedger(Path(tmp) / "events.sqlite3")
    for ev in [
        NativeEvent(
            "DOM.attributeModified",
            "browser_cdp",
            "browser.dom.node:42",
            0.35,
            node_id=42,
            payload={"name": "aria-expanded", "value": "true"},
        ),
        NativeEvent(
            "DOM.childNodeInserted",
            "browser_cdp",
            "browser.dom.node:10",
            0.55,
            node_id=10,
            payload={"inserted_node": "dialog"},
        ),
        NativeEvent(
            "DOM.documentUpdated",
            "browser_cdp",
            "browser.document",
            0.90,
            payload={"document_generation": 2},
        ),
    ]:
        ledger.append(ev)
    print("Event ledger count:", ledger.count())
    for row in ledger.recent(min_significance=0.5):
        print(row["kind"], f"sig={row['significance']:.2f}", row["target"])
