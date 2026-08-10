from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class NativeEvent:
    kind: str
    source: str
    target: str
    significance: float
    timestamp: float = field(default_factory=time.time)
    node_id: Optional[int] = None
    backend_node_id: Optional[int] = None
    hwnd: Optional[int] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class EventLedger:
    """Append-only native event ledger. Events signal *where to verify*, not truth."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    significance REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    node_id INTEGER,
                    backend_node_id INTEGER,
                    hwnd INTEGER,
                    payload_json TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind, timestamp)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_target ON events(target, timestamp)"
            )

    def append(self, event: NativeEvent) -> str:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO events (
                    id, kind, source, target, significance, timestamp,
                    node_id, backend_node_id, hwnd, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event.id,
                    event.kind,
                    event.source,
                    event.target,
                    float(event.significance),
                    float(event.timestamp),
                    event.node_id,
                    event.backend_node_id,
                    event.hwnd,
                    json.dumps(event.payload, ensure_ascii=False, default=str),
                ),
            )
        return event.id

    @staticmethod
    def _row(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "kind": row["kind"],
            "source": row["source"],
            "target": row["target"],
            "significance": row["significance"],
            "timestamp": row["timestamp"],
            "node_id": row["node_id"],
            "backend_node_id": row["backend_node_id"],
            "hwnd": row["hwnd"],
            "payload": json.loads(row["payload_json"]),
        }

    def recent(
        self,
        *,
        limit: int = 100,
        kind: Optional[str] = None,
        target: Optional[str] = None,
        min_significance: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        where = []
        args: List[Any] = []
        if kind is not None:
            where.append("kind = ?")
            args.append(kind)
        if target is not None:
            where.append("target = ?")
            args.append(target)
        if min_significance is not None:
            where.append("significance >= ?")
            args.append(float(min_significance))
        sql = "SELECT * FROM events"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        args.append(int(limit))
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(sql, args).fetchall()
        return [self._row(row) for row in rows]

    def count(self) -> int:
        with closing(self._connect()) as conn, conn:
            return int(conn.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    def compact(self, *, older_than: float, keep_significance_at_least: float = 0.75) -> int:
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                """
                DELETE FROM events
                WHERE timestamp < ? AND significance < ?
            """,
                (float(older_than), float(keep_significance_at_least)),
            )
            return int(cur.rowcount)
