"""
database.py — SQLite database manager for CMMS local factory data.
Thread-safe singleton pattern. Stores worker profiles, task records.
"""

import sqlite3
import threading
import os
from datetime import date
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_factory.db")


class DatabaseManager:
    """Thread-safe singleton managing the local SQLite database."""

    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._conn: Optional[sqlite3.Connection] = None
                    cls._instance._init_lock = threading.Lock()
        return cls._instance

    # ── Connection ──────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def init_db(self) -> None:
        """Create tables if they don't exist."""
        with self._init_lock:
            conn = self._get_conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS workers (
                    phone            TEXT PRIMARY KEY,
                    name             TEXT NOT NULL,
                    contract_type    TEXT NOT NULL CHECK(contract_type IN ('CDD','CDI')),
                    contract_end_date TEXT NOT NULL,
                    recovery_balance REAL DEFAULT 0.0,
                    is_active        INTEGER DEFAULT 1 CHECK(is_active IN (0,1))
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_description   TEXT NOT NULL,
                    assigned_workers  TEXT NOT NULL,
                    estimated_duration INTEGER NOT NULL,
                    status            TEXT NOT NULL DEFAULT 'PENDING'
                                        CHECK(status IN ('PENDING','IN_PROGRESS','COMPLETED','FAILED')),
                    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    # ── Workers ─────────────────────────────────────────────────

    def get_workers(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM workers ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    def get_active_workers(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM workers WHERE is_active = 1 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    def add_worker(
        self,
        phone: str,
        name: str,
        contract_type: str,
        contract_end_date: str,
        recovery_balance: float = 0.0,
        is_active: int = 1,
    ) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                """INSERT OR IGNORE INTO workers
                   (phone, name, contract_type, contract_end_date, recovery_balance, is_active)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (phone, name, contract_type, contract_end_date, recovery_balance, is_active),
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[DB] add_worker error: {e}")
            return False

    def update_worker_status(self, phone: str, is_active: int) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                "UPDATE workers SET is_active = ? WHERE phone = ?",
                (is_active, phone),
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[DB] update_worker_status error: {e}")
            return False

    def set_recovery_day(self, phone: str) -> bool:
        """Grant a recovery day — deactivates worker for the day."""
        try:
            conn = self._get_conn()
            conn.execute(
                """UPDATE workers
                   SET is_active = 0,
                       recovery_balance = recovery_balance + 1
                   WHERE phone = ? AND is_active = 1""",
                (phone,),
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[DB] set_recovery_day error: {e}")
            return False

    def clear_recovery_day(self, phone: str) -> bool:
        """Re-activate a worker after recovery day."""
        try:
            conn = self._get_conn()
            conn.execute(
                "UPDATE workers SET is_active = 1 WHERE phone = ?",
                (phone,),
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[DB] clear_recovery_day error: {e}")
            return False

    def check_cdd_expiry(self) -> list[dict]:
        """Return workers with expired CDD contracts that are still active."""
        today = date.today().isoformat()
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM workers
               WHERE contract_type = 'CDD'
                 AND contract_end_date <= ?
                 AND is_active = 1""",
            (today,),
        ).fetchall()
        return [dict(r) for r in rows]

    def expire_worker(self, phone: str) -> bool:
        """Set worker inactive due to contract expiry."""
        return self.update_worker_status(phone, 0)

    # ── Tasks ───────────────────────────────────────────────────

    def get_tasks(self, status: Optional[str] = None) -> list[dict]:
        conn = self._get_conn()
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def add_task(
        self,
        task_description: str,
        assigned_workers: str,
        estimated_duration: int,
    ) -> Optional[int]:
        """Insert a new task, return its id or None on failure."""
        try:
            conn = self._get_conn()
            cur = conn.execute(
                """INSERT INTO tasks
                   (task_description, assigned_workers, estimated_duration)
                   VALUES (?, ?, ?)""",
                (task_description, assigned_workers, estimated_duration),
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"[DB] add_task error: {e}")
            return None

    def update_task_status(self, task_id: int, status: str) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                "UPDATE tasks SET status = ? WHERE id = ?",
                (status, task_id),
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[DB] update_task_status error: {e}")
            return False

    def get_tasks_by_worker(self, phone: str) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM tasks
               WHERE assigned_workers LIKE ?
               ORDER BY created_at DESC""",
            (f"%{phone}%",),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_task_statistics(self) -> dict:
        conn = self._get_conn()
        row = conn.execute(
            """SELECT
                   COUNT(*) AS total,
                   SUM(CASE WHEN status='PENDING' THEN 1 ELSE 0 END) AS pending,
                   SUM(CASE WHEN status='IN_PROGRESS' THEN 1 ELSE 0 END) AS in_progress,
                   SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) AS completed,
                   SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) AS failed
               FROM tasks"""
        ).fetchone()
        return dict(row) if row else {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "failed": 0}

    # ── Seed / Lifecycle ────────────────────────────────────────

    def seed_default_workers(self) -> None:
        """Insert 5 placeholder technicians if workers table is empty."""
        conn = self._get_conn()
        count = conn.execute("SELECT COUNT(*) FROM workers").fetchone()[0]
        if count > 0:
            return
        defaults = [
            ("+213555000001", "Technician 1", "CDD", "2026-12-31", 0.0, 1),
            ("+213555000002", "Technician 2", "CDI", "2026-12-31", 0.0, 1),
            ("+213555000003", "Technician 3", "CDD", "2026-06-15", 0.0, 1),
            ("+213555000004", "Technician 4", "CDI", "2026-12-31", 0.0, 1),
            ("+213555000005", "Technician 5", "CDD", "2026-12-31", 0.0, 1),
        ]
        conn.executemany(
            """INSERT OR IGNORE INTO workers
               (phone, name, contract_type, contract_end_date, recovery_balance, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            defaults,
        )
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
