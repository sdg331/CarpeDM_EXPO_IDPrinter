"""Local SQLite state for kiosk sessions and side-effect idempotency.

The kiosk is a single-device system, so SQLite is deliberately used instead of a
network database. It survives browser refreshes and process restarts while keeping
visitor data on the Raspberry Pi.

No raw face image or face embedding is stored here.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT / "data" / "kiosk.sqlite3"

TEAM_LABELS = {
    "development": "개발팀",
    "ai": "AI팀",
    "design": "디자인팀",
    "planning": "기획팀",
    "marketing": "마케팅팀",
    "hr": "인사팀",
}
AI_MODES = {"A", "B"}


class StoreError(Exception):
    pass


class SessionNotFound(StoreError):
    pass


class OperationConflict(StoreError):
    pass


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class KioskStore:
    def __init__(self, path: str | Path | None = None):
        configured = path or os.getenv("KIOSK_DB_PATH")
        self.path = Path(configured) if configured else DEFAULT_DB_PATH

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("PRAGMA busy_timeout = 5000")
        con.execute("PRAGMA journal_mode = WAL")
        return con

    def init(self) -> None:
        with self._connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS counters (
                    day TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    team_id TEXT NOT NULL,
                    ai_mode TEXT NOT NULL,
                    char_id TEXT,
                    profile_id TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS card_bindings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_uid TEXT NOT NULL,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    operation_id TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    released_at TEXT
                );

                CREATE UNIQUE INDEX IF NOT EXISTS ux_card_active
                    ON card_bindings(card_uid) WHERE active = 1;
                CREATE UNIQUE INDEX IF NOT EXISTS ux_session_card_active
                    ON card_bindings(session_id) WHERE active = 1;
                CREATE UNIQUE INDEX IF NOT EXISTS ux_card_operation
                    ON card_bindings(operation_id) WHERE operation_id IS NOT NULL;

                CREATE TABLE IF NOT EXISTS operations (
                    operation_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    session_id TEXT REFERENCES sessions(session_id),
                    status TEXT NOT NULL,
                    result_json TEXT,
                    error_code TEXT,
                    retryable INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def create_session(
        self,
        *,
        name: str,
        team_id: str,
        ai_mode: str,
        char_id: str | None = None,
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        if team_id not in TEAM_LABELS:
            raise ValueError("unknown team_id")
        if ai_mode not in AI_MODES:
            raise ValueError("unknown ai_mode")

        clean_name = name.strip()
        if not 1 <= len(clean_name) <= 10:
            raise ValueError("name must be 1..10 characters")

        now = _now()
        day = datetime.now().strftime("%y%m%d")
        with self._connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT value FROM counters WHERE day = ?", (day,)).fetchone()
            seq = (int(row["value"]) if row else 0) + 1
            if seq > 9999:
                con.execute("ROLLBACK")
                raise StoreError("daily session counter exhausted")
            con.execute(
                """
                INSERT INTO counters(day, value) VALUES (?, ?)
                ON CONFLICT(day) DO UPDATE SET value = excluded.value
                """,
                (day, seq),
            )
            session_id = f"MW{day}{seq:04d}"
            con.execute(
                """
                INSERT INTO sessions(
                    session_id, name, team_id, ai_mode, char_id, profile_id,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    clean_name,
                    team_id,
                    ai_mode,
                    char_id,
                    profile_id,
                    "profile_ready" if (char_id or profile_id) else "created",
                    now,
                    now,
                ),
            )
            con.execute("COMMIT")
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> dict[str, Any]:
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if not row:
            raise SessionNotFound(session_id)
        return dict(row)

    def set_profile_result(
        self,
        session_id: str,
        *,
        char_id: str | None = None,
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        if not char_id and not profile_id:
            raise ValueError("char_id or profile_id is required")
        now = _now()
        with self._connect() as con:
            cur = con.execute(
                """
                UPDATE sessions
                SET char_id = COALESCE(?, char_id),
                    profile_id = COALESCE(?, profile_id),
                    status = 'profile_ready',
                    updated_at = ?
                WHERE session_id = ?
                """,
                (char_id, profile_id, now, session_id),
            )
            if cur.rowcount != 1:
                raise SessionNotFound(session_id)
        return self.get_session(session_id)

    def get_operation(self, operation_id: str, kind: str | None = None) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM operations WHERE operation_id = ?", (operation_id,)
            ).fetchone()
        if not row:
            return None
        out = dict(row)
        if kind is not None and out["kind"] != kind:
            raise OperationConflict(
                f"operation {operation_id} belongs to {out['kind']}, not {kind}"
            )
        if out["result_json"]:
            out["result"] = json.loads(out["result_json"])
        else:
            out["result"] = None
        out["retryable"] = bool(out["retryable"])
        return out

    def begin_operation(
        self, operation_id: str, *, kind: str, session_id: str | None
    ) -> dict[str, Any]:
        now = _now()
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO operations(
                    operation_id, kind, session_id, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, 'running', ?, ?)
                """,
                (operation_id, kind, session_id, now, now),
            )
        return self.get_operation(operation_id, kind)  # type: ignore[return-value]

    def restart_operation(self, operation_id: str, *, kind: str) -> dict[str, Any]:
        op = self.get_operation(operation_id, kind)
        if not op:
            raise StoreError("operation does not exist")
        if op["status"] != "retryable_error":
            return op
        now = _now()
        with self._connect() as con:
            con.execute(
                """
                UPDATE operations
                SET status = 'running', error_code = NULL, retryable = 0, updated_at = ?
                WHERE operation_id = ?
                """,
                (now, operation_id),
            )
        return self.get_operation(operation_id, kind)  # type: ignore[return-value]

    def finish_operation(
        self,
        operation_id: str,
        *,
        kind: str,
        status: str,
        result: dict[str, Any] | None = None,
        error_code: str | None = None,
        retryable: bool = False,
    ) -> dict[str, Any]:
        if status not in {"success", "retryable_error", "unknown", "error"}:
            raise ValueError("invalid operation status")
        self.get_operation(operation_id, kind)
        now = _now()
        with self._connect() as con:
            con.execute(
                """
                UPDATE operations
                SET status = ?, result_json = ?, error_code = ?, retryable = ?, updated_at = ?
                WHERE operation_id = ?
                """,
                (
                    status,
                    json.dumps(result, ensure_ascii=False) if result is not None else None,
                    error_code,
                    1 if retryable else 0,
                    now,
                    operation_id,
                ),
            )
        return self.get_operation(operation_id, kind)  # type: ignore[return-value]

    def bind_card(
        self, *, session_id: str, card_uid: str, operation_id: str
    ) -> dict[str, Any]:
        self.get_session(session_id)
        uid = card_uid.strip().upper()
        if not uid:
            raise ValueError("empty card uid")
        now = _now()
        with self._connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                """
                UPDATE card_bindings
                SET active = 0, released_at = ?
                WHERE active = 1 AND (card_uid = ? OR session_id = ?)
                """,
                (now, uid, session_id),
            )
            con.execute(
                """
                INSERT INTO card_bindings(
                    card_uid, session_id, operation_id, active, created_at
                ) VALUES (?, ?, ?, 1, ?)
                """,
                (uid, session_id, operation_id, now),
            )
            con.execute(
                """
                UPDATE sessions
                SET status = 'active', updated_at = ?
                WHERE session_id = ?
                """,
                (now, session_id),
            )
            con.execute("COMMIT")
        return {"card_uid": uid, "session_id": session_id}

    def binding_for_operation(self, operation_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute(
                """
                SELECT card_uid, session_id, active, created_at
                FROM card_bindings
                WHERE operation_id = ?
                """,
                (operation_id,),
            ).fetchone()
        return dict(row) if row else None

    def resolve_card(self, card_uid: str) -> dict[str, Any] | None:
        uid = card_uid.strip().upper()
        with self._connect() as con:
            row = con.execute(
                """
                SELECT s.*
                FROM card_bindings b
                JOIN sessions s ON s.session_id = b.session_id
                WHERE b.card_uid = ? AND b.active = 1
                """,
                (uid,),
            ).fetchone()
        return dict(row) if row else None

    def release_session(self, session_id: str) -> None:
        now = _now()
        with self._connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                """
                UPDATE card_bindings
                SET active = 0, released_at = ?
                WHERE session_id = ? AND active = 1
                """,
                (now, session_id),
            )
            cur = con.execute(
                """
                UPDATE sessions
                SET status = 'checkout_complete', updated_at = ?
                WHERE session_id = ?
                """,
                (now, session_id),
            )
            if cur.rowcount != 1:
                con.execute("ROLLBACK")
                raise SessionNotFound(session_id)
            con.execute("COMMIT")

    def health(self) -> dict[str, Any]:
        try:
            self.init()
            with self._connect() as con:
                con.execute("SELECT 1").fetchone()
            return {"ready": True, "backend": "sqlite"}
        except Exception as exc:
            return {"ready": False, "backend": "sqlite", "detail": str(exc)}
