import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class TaskLog:
    """
    Simple SQLite-backed task log.

    Table: tasks
      - id INTEGER PRIMARY KEY AUTOINCREMENT
      - goal TEXT
      - file_path TEXT
      - status TEXT
      - message TEXT
      - created_at TEXT (ISO8601)
      - updated_at TEXT (ISO8601)
    """

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_task(self, goal: str, file_path: str) -> int:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO tasks (goal, file_path, status, message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (goal, file_path, "running", "", now, now),
            )
            conn.commit()
            return cur.lastrowid

    def complete_task(self, task_id: int, status: str, message: str = "") -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE tasks
                SET status = ?, message = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, message, now, task_id),
            )
            conn.commit()

    def list_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, goal, file_path, status, message, created_at, updated_at
                FROM tasks
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()

        keys = ["id", "goal", "file_path", "status", "message", "created_at", "updated_at"]
        return [dict(zip(keys, row)) for row in rows]
