
"""SQLite database manager for TG Contact Extractor."""
import sqlite3
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH, DB_VERSION
from utils.logger import get_logger
from utils.helpers import now_str

log = get_logger("database")


class Database:
    """Thread-safe SQLite wrapper."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    @contextmanager
    def _cursor(self):
        conn = self._conn()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def _init_db(self):
        """Create tables if they do not exist."""
        with self._cursor() as cur:
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE TABLE IF NOT EXISTS accounts (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone        TEXT UNIQUE NOT NULL,
                    first_name   TEXT,
                    last_name    TEXT,
                    username     TEXT,
                    user_id      INTEGER,
                    api_id       TEXT,
                    connected_at TEXT,
                    is_active    INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS extracted_users (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id           INTEGER UNIQUE NOT NULL,
                    first_name        TEXT,
                    last_name         TEXT,
                    full_name         TEXT,
                    username          TEXT,
                    phone             TEXT,
                    is_contact        INTEGER DEFAULT 0,
                    last_message_date TEXT,
                    chat_type         TEXT DEFAULT 'private',
                    extraction_date   TEXT,
                    updated_at        TEXT
                );

                CREATE TABLE IF NOT EXISTS extraction_history (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_phone   TEXT,
                    started_at      TEXT,
                    finished_at     TEXT,
                    total_found     INTEGER DEFAULT 0,
                    status          TEXT DEFAULT 'running'
                );
            """)
        log.info("Database initialised at %s", self.db_path)

    # ── Settings ────────────────────────────────────────────────────────
    def get_setting(self, key: str, default: str = "") -> str:
        with self._cursor() as cur:
            cur.execute("SELECT value FROM app_settings WHERE key=?", (key,))
            row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self._cursor() as cur:
            cur.execute(
                "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?,?)",
                (key, value),
            )

    # ── Account ─────────────────────────────────────────────────────────
    def save_account(self, phone: str, first_name: str = None,
                     last_name: str = None, username: str = None,
                     user_id: int = None, api_id: str = None):
        with self._cursor() as cur:
            cur.execute("""
                INSERT INTO accounts (phone, first_name, last_name, username, user_id, api_id, connected_at)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(phone) DO UPDATE SET
                    first_name=excluded.first_name,
                    last_name=excluded.last_name,
                    username=excluded.username,
                    user_id=excluded.user_id,
                    api_id=excluded.api_id,
                    connected_at=excluded.connected_at,
                    is_active=1
            """, (phone, first_name, last_name, username, user_id, api_id, now_str()))
        log.info("Account saved: %s", phone)

    def get_active_account(self) -> Optional[Dict]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM accounts WHERE is_active=1 ORDER BY connected_at DESC LIMIT 1")
            row = cur.fetchone()
        return dict(row) if row else None

    def deactivate_account(self, phone: str):
        with self._cursor() as cur:
            cur.execute("UPDATE accounts SET is_active=0 WHERE phone=?", (phone,))

    # ── Users ────────────────────────────────────────────────────────────
    def upsert_user(self, user_data: Dict[str, Any]):
        with self._cursor() as cur:
            cur.execute("""
                INSERT INTO extracted_users
                    (user_id, first_name, last_name, full_name, username,
                     phone, is_contact, last_message_date, chat_type,
                     extraction_date, updated_at)
                VALUES (:user_id,:first_name,:last_name,:full_name,:username,
                        :phone,:is_contact,:last_message_date,:chat_type,
                        :extraction_date,:updated_at)
                ON CONFLICT(user_id) DO UPDATE SET
                    first_name=excluded.first_name,
                    last_name=excluded.last_name,
                    full_name=excluded.full_name,
                    username=COALESCE(excluded.username, username),
                    phone=COALESCE(excluded.phone, phone),
                    is_contact=excluded.is_contact,
                    last_message_date=excluded.last_message_date,
                    updated_at=excluded.updated_at
            """, user_data)

    def get_all_users(self, filter_key: str = "all") -> List[Dict]:
        query = "SELECT * FROM extracted_users"
        params = ()
        if filter_key == "with_username":
            query += " WHERE username IS NOT NULL AND username != ''"
        elif filter_key == "without_username":
            query += " WHERE username IS NULL OR username = ''"
        elif filter_key == "with_phone":
            query += " WHERE phone IS NOT NULL AND phone != ''"
        elif filter_key == "without_phone":
            query += " WHERE phone IS NULL OR phone = ''"
        elif filter_key == "saved_contacts":
            query += " WHERE is_contact=1"
        elif filter_key == "non_saved":
            query += " WHERE is_contact=0"
        query += " ORDER BY full_name"
        with self._cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_user_count(self) -> int:
        with self._cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM extracted_users")
            return cur.fetchone()[0]

    def get_stats(self) -> Dict[str, int]:
        with self._cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM extracted_users"); total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM extracted_users WHERE username IS NOT NULL AND username!=''"); w_user = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM extracted_users WHERE phone IS NOT NULL AND phone!=''"); w_phone = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM extracted_users WHERE is_contact=1"); saved = cur.fetchone()[0]
        return {
            "total": total,
            "with_username": w_user,
            "without_username": total - w_user,
            "with_phone": w_phone,
            "without_phone": total - w_phone,
            "saved_contacts": saved,
            "non_saved": total - saved,
        }

    def clear_users(self):
        with self._cursor() as cur:
            cur.execute("DELETE FROM extracted_users")
        log.info("All extracted users cleared.")

    def get_users_paginated(self, offset: int = 0, limit: int = 100) -> List[Dict]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM extracted_users ORDER BY full_name LIMIT ? OFFSET ?", (limit, offset))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    # ── History ─────────────────────────────────────────────────────────
    def start_extraction_history(self, account_phone: str) -> int:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO extraction_history (account_phone, started_at, status) VALUES (?,?,?)",
                (account_phone, now_str(), "running"),
            )
            return cur.lastrowid

    def finish_extraction_history(self, history_id: int, total_found: int, status: str = "completed"):
        with self._cursor() as cur:
            cur.execute(
                "UPDATE extraction_history SET finished_at=?, total_found=?, status=? WHERE id=?",
                (now_str(), total_found, status, history_id),
            )

    def get_history(self) -> List[Dict]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM extraction_history ORDER BY started_at DESC LIMIT 50")
            rows = cur.fetchall()
        return [dict(r) for r in rows]
