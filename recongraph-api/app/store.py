"""SQLite persistence for reconciliation runs and IMS actions (F2).

Replaces the in-memory ``_runs_store`` dict with a small, dependency-free
``sqlite3`` store. The schema is minimal and additive: the engine result is
stored as JSON, and IMS/ITC decisions are stored per packet.

Configure via the ``RECONGRAPH_DB_PATH`` environment variable (default:
``./data/recongraph.db``).
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


def _db_path() -> Path:
    env = os.environ.get("RECONGRAPH_DB_PATH", "./data/recongraph.db")
    return Path(env)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    engine_version TEXT,
    config_hash TEXT,
    result_json TEXT
);

CREATE TABLE IF NOT EXISTS packet_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    packet_id TEXT NOT NULL,
    ims_action TEXT NOT NULL,
    status TEXT NOT NULL,
    itc_availability TEXT,
    itc_claim_period TEXT,
    reason_itc_unavailability TEXT,
    reviewer_id TEXT,
    comments TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(run_id, packet_id)
);
"""


class Store:
    def __init__(self, db_path: str | os.PathLike | None = None):
        path = Path(db_path) if db_path else _db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ---- runs -----------------------------------------------------------
    def save_run(
        self,
        run_id: str,
        created_at: str,
        status: str,
        result: dict[str, Any],
        engine_version: str | None = None,
        config_hash: str | None = None,
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO runs "
            "(run_id, created_at, status, engine_version, config_hash, result_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, created_at, status, engine_version, config_hash,
             json.dumps(result)),
        )
        self._conn.commit()

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            return None
        return {
            "run_id": row["run_id"],
            "created_at": row["created_at"],
            "status": row["status"],
            "engine_version": row["engine_version"],
            "config_hash": row["config_hash"],
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
        }

    def update_run_status(self, run_id: str, status: str) -> None:
        self._conn.execute(
            "UPDATE runs SET status = ? WHERE run_id = ?", (status, run_id)
        )
        self._conn.commit()

    def list_runs(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT run_id, created_at, status, engine_version, config_hash "
            "FROM runs ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]

    # ---- packet actions -------------------------------------------------
    def apply_action(
        self,
        run_id: str,
        packet_id: str,
        action: dict[str, Any],
    ) -> None:
        self._conn.execute(
            "INSERT INTO packet_actions "
            "(run_id, packet_id, ims_action, status, itc_availability, "
            " itc_claim_period, reason_itc_unavailability, reviewer_id, comments, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(run_id, packet_id) DO UPDATE SET "
            "ims_action=excluded.ims_action, status=excluded.status, "
            "itc_availability=excluded.itc_availability, "
            "itc_claim_period=excluded.itc_claim_period, "
            "reason_itc_unavailability=excluded.reason_itc_unavailability, "
            "reviewer_id=excluded.reviewer_id, comments=excluded.comments, "
            "updated_at=excluded.updated_at",
            (
                run_id,
                packet_id,
                action["action"],
                action["status"],
                action.get("itc_availability"),
                action.get("itc_claim_period"),
                action.get("reason_itc_unavailability"),
                action.get("reviewer_id"),
                action.get("comments"),
                action["updated_at"],
            ),
        )
        self._conn.commit()

    def get_packet_action(self, run_id: str, packet_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM packet_actions WHERE run_id = ? AND packet_id = ?",
            (run_id, packet_id),
        ).fetchone()
        return dict(row) if row else None

    def get_run_actions(self, run_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM packet_actions WHERE run_id = ? ORDER BY updated_at DESC",
            (run_id,),
        ).fetchall()
        return [dict(row) for row in rows]
