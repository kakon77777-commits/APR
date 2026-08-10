from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionReceipt:
    action_id: str
    action_name: str
    started_at: float
    executed_at: float
    readiness: str
    result_repr: str = ""
    retry_count: int = 0
    parent_execution_id: Optional[str] = None
    status: str = "executed"
    outcome: Optional[str] = None
    completed_at: Optional[float] = None
    pre_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class ExecutionLedger:
    """Persistent action-execution receipts and evidence links."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS executions (
                    id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    executed_at REAL NOT NULL,
                    readiness TEXT NOT NULL,
                    result_repr TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    parent_execution_id TEXT,
                    status TEXT NOT NULL,
                    outcome TEXT,
                    completed_at REAL,
                    pre_state_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_evidence (
                    execution_id TEXT NOT NULL,
                    evidence_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    PRIMARY KEY (execution_id, evidence_id, role)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_exec_action ON executions(action_id, executed_at)"
            )

    def upsert(self, receipt: ExecutionReceipt) -> str:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO executions (
                    id, action_id, action_name, started_at, executed_at,
                    readiness, result_repr, retry_count, parent_execution_id,
                    status, outcome, completed_at, pre_state_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.id,
                    receipt.action_id,
                    receipt.action_name,
                    receipt.started_at,
                    receipt.executed_at,
                    receipt.readiness,
                    receipt.result_repr,
                    receipt.retry_count,
                    receipt.parent_execution_id,
                    receipt.status,
                    receipt.outcome,
                    receipt.completed_at,
                    json.dumps(receipt.pre_state, ensure_ascii=False, default=str),
                    json.dumps(receipt.metadata, ensure_ascii=False, default=str),
                ),
            )
        return receipt.id

    def get(self, execution_id: str) -> Optional[ExecutionReceipt]:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT * FROM executions WHERE id = ?",
                (execution_id,),
            ).fetchone()
        if row is None:
            return None
        return ExecutionReceipt(
            id=row["id"],
            action_id=row["action_id"],
            action_name=row["action_name"],
            started_at=row["started_at"],
            executed_at=row["executed_at"],
            readiness=row["readiness"],
            result_repr=row["result_repr"],
            retry_count=row["retry_count"],
            parent_execution_id=row["parent_execution_id"],
            status=row["status"],
            outcome=row["outcome"],
            completed_at=row["completed_at"],
            pre_state=json.loads(row["pre_state_json"]),
            metadata=json.loads(row["metadata_json"]),
        )

    def link_evidence(
        self,
        execution_id: str,
        evidence_id: str,
        *,
        role: str = "postcondition",
    ) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO execution_evidence (
                    execution_id, evidence_id, role
                ) VALUES (?, ?, ?)
                """,
                (execution_id, evidence_id, role),
            )

    def evidence_links(self, execution_id: str) -> List[Dict[str, str]]:
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                """
                SELECT execution_id, evidence_id, role
                FROM execution_evidence
                WHERE execution_id = ?
                ORDER BY evidence_id
                """,
                (execution_id,),
            ).fetchall()
        return [
            {
                "execution_id": row["execution_id"],
                "evidence_id": row["evidence_id"],
                "role": row["role"],
            }
            for row in rows
        ]

    def recent(self, *, action_id: Optional[str] = None, limit: int = 100):
        with closing(self._connect()) as conn, conn:
            if action_id is None:
                rows = conn.execute(
                    "SELECT * FROM executions ORDER BY executed_at DESC LIMIT ?",
                    (int(limit),),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM executions
                    WHERE action_id = ?
                    ORDER BY executed_at DESC
                    LIMIT ?
                    """,
                    (action_id, int(limit)),
                ).fetchall()
        return [self.get(row["id"]) for row in rows]
