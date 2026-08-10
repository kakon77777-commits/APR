import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import ExecutionLedger, ExecutionReceipt


class ExecutionLedgerTests(unittest.TestCase):
    def test_receipt_round_trip_and_evidence_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExecutionLedger(Path(tmp) / "exec.sqlite3")
            receipt = ExecutionReceipt(
                action_id="a",
                action_name="Action",
                started_at=time.time(),
                executed_at=time.time(),
                readiness="allow",
                result_repr="ok",
                pre_state={"x": 1},
            )
            ledger.upsert(receipt)
            loaded = ledger.get(receipt.id)
            self.assertEqual(loaded.action_id, "a")
            self.assertEqual(loaded.pre_state, {"x": 1})

            ledger.link_evidence(receipt.id, "e1")
            links = ledger.evidence_links(receipt.id)
            self.assertEqual(links[0]["evidence_id"], "e1")


if __name__ == "__main__":
    unittest.main()
