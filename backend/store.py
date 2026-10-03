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
import threading
from contextlib import closing, contextmanager
from datetime import datetime, timedelta
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
        self._card_lock = threading.RLock()

    @contextmanager
    def card_access(self):
        """Serialize local card ownership changes with final device submission.

        The kiosk runs one worker because portraits/previews are memory-only.
        Network requests, rendering, and NFC waits happen outside this guard.
        """
        with self._card_lock:
            yield

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        self.path.chmod(0o600)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("PRAGMA busy_timeout = 5000")
        con.execute("PRAGMA journal_mode = WAL")
        return con

    def init(self) -> None:
        with closing(self._connect()) as con:
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

                CREATE TABLE IF NOT EXISTS mirrorting_links (
                    session_id TEXT PRIMARY KEY REFERENCES sessions(session_id),
                    mirror_session_id INTEGER NOT NULL UNIQUE,
                    access_token TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS operator_resolutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    resolved_at TEXT NOT NULL
                );

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
        operation_id: str | None = None,
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
        with closing(self._connect()) as con:
            con.execute("BEGIN IMMEDIATE")
            if operation_id:
                existing = con.execute("SELECT * FROM operations WHERE operation_id=?", (operation_id,)).fetchone()
                if existing:
                    if existing['kind'] != 'nfc_register':
                        raise OperationConflict("operation kind changed")
                    original = con.execute("SELECT * FROM sessions WHERE session_id=?", (existing['session_id'],)).fetchone()
                    if not original or any(original[key] != value for key, value in {
                        'name': clean_name, 'team_id': team_id, 'ai_mode': ai_mode,
                        'char_id': char_id, 'profile_id': profile_id,
                    }.items()):
                        raise OperationConflict("registration payload changed")
                    con.execute("COMMIT")
                    return {**dict(original), 'claimed': False}
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
            if operation_id:
                con.execute(
                    "INSERT INTO operations(operation_id,kind,session_id,status,created_at,updated_at) "
                    "VALUES (?,'nfc_register',?,'running',?,?)", (operation_id, session_id, now, now),
                )
            con.execute("COMMIT")
        result = self.get_session(session_id)
        if operation_id:
            result['claimed'] = True
        return result

    def get_session(self, session_id: str) -> dict[str, Any]:
        with closing(self._connect()) as con:
            row = con.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if not row or row["status"] == "expired":
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
        with closing(self._connect()) as con:
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
        with closing(self._connect()) as con:
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
        with closing(self._connect()) as con:
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

    def claim_operation(
        self, operation_id: str, *, kind: str, session_id: str | None,
        unique_session: bool = False,
    ) -> dict[str, Any]:
        """Atomically acquire one execution; callers must honor ``claimed``.

        Print claims additionally cover the session, so a browser refresh or a
        different operation ID cannot print the same visitor again. A failed
        render (before device access) can be explicitly retried under the same ID.
        """
        now = _now()
        with closing(self._connect()) as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT * FROM operations WHERE operation_id = ?", (operation_id,)
            ).fetchone()
            if row and (row['kind'] != kind or row['session_id'] != session_id):
                raise OperationConflict("operation request does not match its original session")
            if row is None and unique_session:
                row = con.execute(
                    "SELECT * FROM operations WHERE kind = ? AND session_id = ? ORDER BY created_at LIMIT 1",
                    (kind, session_id),
                ).fetchone()
            claimed = row is None
            selected_id = row['operation_id'] if row else operation_id
            if row is None:
                con.execute(
                    "INSERT INTO operations(operation_id,kind,session_id,status,created_at,updated_at) "
                    "VALUES (?,?,?,'running',?,?)", (operation_id, kind, session_id, now, now),
                )
            elif row['status'] == 'retryable_error':
                con.execute(
                    "UPDATE operations SET status='running',error_code=NULL,retryable=0,updated_at=? "
                    "WHERE operation_id=?", (now, selected_id),
                )
                claimed = True
            con.execute("COMMIT")
        result = self.get_operation(selected_id, kind)
        result['claimed'] = claimed
        return result

    def print_operation(self, session_id: str, kind: str = 'badge_print') -> dict[str, Any] | None:
        with closing(self._connect()) as con:
            row = con.execute(
                "SELECT operation_id FROM operations WHERE kind=? AND session_id=? ORDER BY created_at LIMIT 1",
                (kind, session_id),
            ).fetchone()
        return self.get_operation(row['operation_id']) if row else None

    def restart_operation(self, operation_id: str, *, kind: str) -> dict[str, Any]:
        op = self.get_operation(operation_id, kind)
        if not op:
            raise StoreError("operation does not exist")
        if op["status"] != "retryable_error":
            return op
        now = _now()
        with closing(self._connect()) as con:
            changed = con.execute(
                """
                UPDATE operations
                SET status = 'running', error_code = NULL, retryable = 0, updated_at = ?
                WHERE operation_id = ? AND kind = ? AND status = 'retryable_error'
                """,
                (now, operation_id, kind),
            ).rowcount
        result = self.get_operation(operation_id, kind)
        result['claimed'] = changed == 1
        return result  # type: ignore[return-value]

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
        if self.get_operation(operation_id, kind) is None:
            raise StoreError("operation does not exist")
        now = _now()
        with closing(self._connect()) as con:
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
        with self.card_access():
            return self._bind_card(session_id=session_id, card_uid=card_uid, operation_id=operation_id)

    def _bind_card(
        self, *, session_id: str, card_uid: str, operation_id: str
    ) -> dict[str, Any]:
        self.get_session(session_id)
        uid = card_uid.strip().upper()
        if not uid:
            raise ValueError("empty card uid")
        now = _now()
        with closing(self._connect()) as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "UPDATE sessions SET status='replaced',updated_at=? WHERE session_id IN "
                "(SELECT session_id FROM card_bindings WHERE card_uid=? AND active=1 AND session_id!=?)",
                (now, uid, session_id),
            )
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
        with closing(self._connect()) as con:
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
        with closing(self._connect()) as con:
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

    def active_card(self, session_id: str) -> bool:
        with closing(self._connect()) as con:
            return con.execute(
                'SELECT 1 FROM card_bindings WHERE session_id=? AND active=1', (session_id,),
            ).fetchone() is not None

    def release_session(self, session_id: str) -> None:
        with self.card_access():
            self._release_session(session_id)

    def _release_session(self, session_id: str) -> None:
        now = _now()
        with closing(self._connect()) as con:
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

    def recover_interrupted_operations(self) -> None:
        """Only call once during single-worker startup, before accepting traffic."""
        with closing(self._connect()) as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "UPDATE operations SET status='unknown',error_code='UNKNOWN_OUTCOME',retryable=0,updated_at=? "
                "WHERE status='running' AND kind IN ('badge_print','report_print')", (_now(),),
            )
            con.execute(
                "UPDATE operations SET status='retryable_error',error_code='NFC_INTERRUPTED',retryable=1,updated_at=? "
                "WHERE status='running' AND kind='nfc_register'", (_now(),),
            )
            con.execute("COMMIT")

    def resolve_unknown_operation(self, operation_id: str, *, outcome: str) -> dict[str, Any]:
        """Local operator only, after checking the physical paper/device queue."""
        if outcome not in {'printed', 'not_printed'}:
            raise ValueError('outcome must be printed or not_printed')
        now = _now()
        with closing(self._connect()) as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM operations WHERE operation_id=?', (operation_id,)).fetchone()
            if not row or row['kind'] not in {'badge_print', 'report_print'} or row['status'] != 'unknown':
                raise OperationConflict('only unknown print operations can be resolved')
            session = con.execute('SELECT * FROM sessions WHERE session_id=?', (row['session_id'],)).fetchone()
            if not session or session['status'] == 'expired':
                raise OperationConflict('expired session cannot be resumed')
            if outcome == 'not_printed':
                binding = con.execute('SELECT 1 FROM card_bindings WHERE session_id=? AND active=1', (row['session_id'],)).fetchone()
                if not binding:
                    raise OperationConflict('card was released or assigned to another visitor')
                con.execute(
                    "UPDATE operations SET status='retryable_error',error_code='PRINT_RETRY_AUTHORIZED',retryable=1,updated_at=? WHERE operation_id=?",
                    (now, operation_id),
                )
            else:
                result = {'status': 'confirmed', 'printJobId': operation_id, 'backend': 'operator_confirmed',
                          'physicalOutput': True, 'completionConfirmed': True}
                con.execute(
                    "UPDATE operations SET status='success',error_code=NULL,retryable=0,result_json=?,updated_at=? WHERE operation_id=?",
                    (json.dumps(result), now, operation_id),
                )
            con.execute('INSERT INTO operator_resolutions(operation_id,outcome,resolved_at) VALUES (?,?,?)', (operation_id, outcome, now))
            con.execute('COMMIT')
        return self.get_operation(operation_id)

    def link_mirrorting(
        self, *, session_id: str, card_uid: str, mirror_session_id: int, access_token: str,
    ) -> dict[str, Any]:
        """Trusted server callback binds one immutable MirrorTing visit to this card visit."""
        if mirror_session_id < 1 or not access_token or len(access_token) > 512:
            raise ValueError('invalid MirrorTing credentials')
        uid = card_uid.strip().upper()
        with closing(self._connect()) as con:
            con.execute('BEGIN IMMEDIATE')
            binding = con.execute(
                "SELECT b.session_id FROM card_bindings b JOIN sessions s ON s.session_id=b.session_id "
                "WHERE b.card_uid=? AND b.session_id=? AND b.active=1 AND s.status!='expired'",
                (uid, session_id),
            ).fetchone()
            if not binding:
                raise OperationConflict('card is no longer bound to this visitor')
            existing = con.execute('SELECT * FROM mirrorting_links WHERE session_id=? OR mirror_session_id=?',
                                   (session_id, mirror_session_id)).fetchall()
            if existing:
                if len(existing) != 1 or existing[0]['session_id'] != session_id or existing[0]['mirror_session_id'] != mirror_session_id or existing[0]['access_token'] != access_token:
                    raise OperationConflict('MirrorTing visit is already linked')
            else:
                con.execute('INSERT INTO mirrorting_links VALUES (?,?,?,?)',
                            (session_id, mirror_session_id, access_token, _now()))
            con.execute('COMMIT')
        return {'sessionId': session_id, 'mirrorSessionId': mirror_session_id}

    def get_mirrorting_link(self, session_id: str) -> dict[str, Any] | None:
        self.get_session(session_id)
        with closing(self._connect()) as con:
            row = con.execute('SELECT * FROM mirrorting_links WHERE session_id=?', (session_id,)).fetchone()
        return dict(row) if row else None

    def purge_expired(self, retention_hours: float = 24) -> dict[str, int]:
        """Remove visitor data while keeping irreversible-operation tombstones."""
        with self.card_access():
            return self._purge_expired(retention_hours)

    def _purge_expired(self, retention_hours: float) -> dict[str, int]:
        if retention_hours <= 0:
            raise ValueError('retention must be positive')
        cutoff = (datetime.now().astimezone() - timedelta(hours=retention_hours)).isoformat(timespec='seconds')
        with closing(self._connect()) as con:
            con.execute('BEGIN IMMEDIATE')
            condition = "SELECT session_id FROM sessions WHERE created_at < ? AND status != 'expired'"
            bindings = con.execute(f'DELETE FROM card_bindings WHERE session_id IN ({condition})', (cutoff,)).rowcount
            links = con.execute(f'DELETE FROM mirrorting_links WHERE session_id IN ({condition})', (cutoff,)).rowcount
            sessions = con.execute(
                "UPDATE sessions SET name='',char_id=NULL,profile_id=NULL,status='expired',updated_at=? "
                "WHERE created_at < ? AND status!='expired'", (_now(), cutoff),
            ).rowcount
            con.execute('COMMIT')
        return {'sessions': sessions, 'bindings': bindings, 'links': links}

    def health(self) -> dict[str, Any]:
        try:
            self.init()
            with closing(self._connect()) as con:
                con.execute("SELECT 1").fetchone()
            return {"ready": True, "backend": "sqlite"}
        except Exception as exc:
            return {"ready": False, "backend": "sqlite", "detail": str(exc)}
