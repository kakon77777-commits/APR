from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .models import Evidence


class EvidenceArchive:
    """
    Persistent evidence metadata + external asset store.

    SQLite stores searchable evidence metadata. Binary assets (ROI PNG crops,
    audio snippets, etc.) are stored as files so the DB stays compact.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.assets_dir = self.root / "assets"
        self.assets_dir.mkdir(exist_ok=True)
        self.db_path = self.root / "evidence.sqlite3"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    claim_key TEXT NOT NULL,
                    observed_value_json TEXT,
                    modality TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    cost REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    pointer TEXT,
                    asset_path TEXT,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence(claim_key, timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source, timestamp)"
            )

    def store_asset(
        self,
        data: bytes,
        *,
        extension: str = ".bin",
        prefix: str = "asset",
    ) -> Path:
        if not extension.startswith("."):
            extension = "." + extension
        name = f"{prefix}-{int(time.time() * 1000)}-{uuid.uuid4().hex[:10]}{extension}"
        path = self.assets_dir / name
        path.write_bytes(data)
        return path

    def record(
        self,
        evidence: Evidence,
        *,
        asset_path: Optional[str | Path] = None,
    ) -> str:
        asset = str(Path(asset_path).resolve()) if asset_path else None
        value_json = json.dumps(
            evidence.observed_value,
            ensure_ascii=False,
            default=str,
        )
        metadata_json = json.dumps(
            evidence.metadata,
            ensure_ascii=False,
            default=str,
        )

        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO evidence (
                    id, claim_key, observed_value_json, modality, source,
                    confidence, cost, timestamp, pointer, asset_path,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.id,
                    evidence.claim_key,
                    value_json,
                    evidence.modality.value,
                    evidence.source,
                    float(evidence.confidence),
                    float(evidence.cost),
                    float(evidence.timestamp),
                    evidence.pointer,
                    asset,
                    metadata_json,
                ),
            )
        return evidence.id

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "claim_key": row["claim_key"],
            "observed_value": json.loads(row["observed_value_json"]),
            "modality": row["modality"],
            "source": row["source"],
            "confidence": row["confidence"],
            "cost": row["cost"],
            "timestamp": row["timestamp"],
            "pointer": row["pointer"],
            "asset_path": row["asset_path"],
            "metadata": json.loads(row["metadata_json"]),
        }

    def get(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT * FROM evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()
        return None if row is None else self._row_to_dict(row)

    def for_claim(self, claim_key: str, *, limit: int = 100) -> List[Dict[str, Any]]:
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                """
                SELECT * FROM evidence
                WHERE claim_key = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (claim_key, int(limit)),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def by_ids(self, evidence_ids: Iterable[str]) -> List[Dict[str, Any]]:
        ids = [str(x) for x in evidence_ids]
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                f"""
                SELECT * FROM evidence
                WHERE id IN ({placeholders})
                ORDER BY timestamp DESC
                """,
                ids,
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def best_for_claim(
        self,
        claim_key: str,
        *,
        require_asset: bool = False,
    ) -> Optional[Dict[str, Any]]:
        candidates = self.for_claim(claim_key, limit=200)
        if require_asset:
            candidates = [
                row
                for row in candidates
                if row.get("asset_path") and Path(row["asset_path"]).exists()
            ]
        if not candidates:
            return None

        # Prefer confidence, then recency. Revisit is about recovering a
        # specific source; ranking should remain transparent and deterministic.
        return max(
            candidates,
            key=lambda row: (
                float(row.get("confidence", 0.0)),
                float(row.get("timestamp", 0.0)),
            ),
        )

    def assets_for_claim(self, claim_key: str, *, limit: int = 100) -> List[Path]:
        rows = self.for_claim(claim_key, limit=limit)
        out: List[Path] = []
        seen = set()
        for row in rows:
            raw = row.get("asset_path")
            if not raw:
                continue
            path = Path(raw)
            if path.exists() and path not in seen:
                out.append(path)
                seen.add(path)
        return out

    def recent(self, *, limit: int = 100) -> List[Dict[str, Any]]:
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "SELECT * FROM evidence ORDER BY timestamp DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def count(self) -> int:
        with closing(self._connect()) as conn, conn:
            return int(conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0])

    def compact(
        self,
        *,
        older_than: float,
        keep_confidence_at_least: float = 0.90,
        protected_ids: Iterable[str] = (),
        delete_unreferenced_assets: bool = True,
    ) -> tuple[int, int]:
        protected = {str(x) for x in protected_ids}
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                """
                SELECT id, asset_path FROM evidence
                WHERE timestamp < ? AND confidence < ?
                """,
                (float(older_than), float(keep_confidence_at_least)),
            ).fetchall()
            doomed = [row for row in rows if row["id"] not in protected]
            if not doomed:
                return 0, 0
            ids = [row["id"] for row in doomed]
            placeholders = ",".join("?" for _ in ids)
            conn.execute(
                f"DELETE FROM evidence WHERE id IN ({placeholders})",
                ids,
            )

        assets_deleted = 0
        if delete_unreferenced_assets:
            for row in doomed:
                raw = row["asset_path"]
                if not raw:
                    continue
                with closing(self._connect()) as conn, conn:
                    refs = int(
                        conn.execute(
                            "SELECT COUNT(*) FROM evidence WHERE asset_path = ?",
                            (raw,),
                        ).fetchone()[0]
                    )
                path = Path(raw)
                if refs == 0 and path.exists() and path.is_file():
                    try:
                        path.unlink()
                        assets_deleted += 1
                    except OSError:
                        pass
        return len(doomed), assets_deleted
