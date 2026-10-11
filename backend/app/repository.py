import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import UTC, datetime

from app.config import Settings


def now() -> str:
    return datetime.now(UTC).isoformat()


class Repository:
    def __init__(self, settings: Settings):
        self.settings = settings
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, title TEXT NOT NULL,
                    created_at TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS usage (id INTEGER PRIMARY KEY, calls INTEGER NOT NULL);
                INSERT OR IGNORE INTO usage VALUES (1, 0);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.settings.database_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def token_hash(self, token: str) -> str:
        return hmac.new(
            self.settings.session_secret.encode(), token.encode(), hashlib.sha256
        ).hexdigest()

    def create_session(self) -> tuple[str, str]:
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute(
                "INSERT INTO sessions VALUES (?, ?, ?)",
                (self.token_hash(token), csrf, time.time() + 86400),
            )
        return token, csrf

    def session(self, token: str | None):
        if not token:
            return None
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE id=? AND expires>?",
                (self.token_hash(token), time.time()),
            ).fetchone()
        return dict(row) if row else None

    def logout(self, sid: str):
        with self.connect() as db:
            db.execute("DELETE FROM sessions WHERE id=?", (sid,))

    def create(self, identifier: str, sid: str, title: str, payload: dict):
        with self.connect() as db:
            db.execute(
                "INSERT INTO incidents VALUES (?, ?, ?, ?, 'queued', ?)",
                (identifier, sid, title, now(), json.dumps(payload)),
            )

    def get(self, identifier: str, sid: str | None = None):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM incidents WHERE id=?" + (" AND session_id=?" if sid else ""),
                (identifier, sid) if sid else (identifier,),
            ).fetchone()
        if not row:
            return None
        result = dict(row)
        result.update(json.loads(result.pop("payload")))
        result.pop("session_id")
        return result

    def update(self, identifier: str, status: str, payload: dict):
        with self.connect() as db:
            db.execute(
                "UPDATE incidents SET status=?, payload=?, title=COALESCE(?,title) WHERE id=?"
                + (" AND status IN ('queued','processing')" if status == "processing" else ""),
                (status, json.dumps(payload), payload.get("report", {}).get("title"), identifier),
            )

    def history(self, sid: str, page: int):
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,title,created_at,status FROM incidents WHERE session_id=? ORDER BY created_at DESC LIMIT 20 OFFSET ?",
                (sid, (page - 1) * 20),
            ).fetchall()
            count = db.execute(
                "SELECT COUNT(*) FROM incidents WHERE session_id=?", (sid,)
            ).fetchone()[0]
        return {"items": [dict(row) for row in rows], "total": count, "page": page}

    def recover(self):
        with self.connect() as db:
            for row in db.execute(
                "SELECT id,payload FROM incidents WHERE status IN ('queued','processing')"
            ).fetchall():
                payload = json.loads(row["payload"])
                payload["error"] = {
                    "code": "interrupted",
                    "message": "Analysis was interrupted by a restart. Retry to create a new investigation.",
                }
                db.execute(
                    "UPDATE incidents SET status='failed',payload=? WHERE id=?",
                    (json.dumps(payload), row["id"]),
                )

    def reserve_model_call(self):
        with self.connect() as db:
            cursor = db.execute(
                "UPDATE usage SET calls=calls+1 WHERE id=1 AND calls<?",
                (self.settings.max_model_calls,),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Demo model-call limit reached. Ask the presenter to review usage."
                )
