"""Per-game persistent memory backed by SQLite.

Stores three kinds of knowledge so the agent can "remember how to do it next
time":

* **facts** - durable key/value knowledge about a game (e.g. boss weakness).
* **events** - a rolling log of what happened (for self-reflection).
* **goals** - long-term objectives and their progress.

A SQLite file per game lives under ``<memory_root>/<game>.db``.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


def _slug(name: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower())
    return safe or "unknown_game"


class GameMemory:
    def __init__(self, root: Path, game_name: str) -> None:
        self.root = Path(root)
        self.game_name = game_name
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / f"{_slug(game_name)}.db"
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS facts (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS goals (
                name TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                progress TEXT,
                updated_at REAL NOT NULL
            );
            """
        )
        self._conn.commit()

    # --- facts ---------------------------------------------------------------
    def remember(self, key: str, value: Any) -> None:
        self._conn.execute(
            "INSERT INTO facts(key, value, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, "
            "updated_at=excluded.updated_at",
            (key, json.dumps(value), time.time()),
        )
        self._conn.commit()

    def recall(self, key: str, default: Any = None) -> Any:
        row = self._conn.execute(
            "SELECT value FROM facts WHERE key=?", (key,)
        ).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    def all_facts(self) -> dict[str, Any]:
        rows = self._conn.execute("SELECT key, value FROM facts").fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}

    # --- events --------------------------------------------------------------
    def log_event(self, kind: str, payload: Optional[dict[str, Any]] = None) -> None:
        self._conn.execute(
            "INSERT INTO events(kind, payload, created_at) VALUES(?,?,?)",
            (kind, json.dumps(payload or {}), time.time()),
        )
        self._conn.commit()

    def recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT kind, payload, created_at FROM events "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "kind": r["kind"],
                "payload": json.loads(r["payload"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # --- goals ---------------------------------------------------------------
    def set_goal(
        self, name: str, status: str = "active", progress: Optional[str] = None
    ) -> None:
        self._conn.execute(
            "INSERT INTO goals(name, status, progress, updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET status=excluded.status, "
            "progress=excluded.progress, updated_at=excluded.updated_at",
            (name, status, progress, time.time()),
        )
        self._conn.commit()

    def goals(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT name, status, progress FROM goals ORDER BY updated_at DESC"
        ).fetchall()
        return [
            {"name": r["name"], "status": r["status"], "progress": r["progress"]}
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()
