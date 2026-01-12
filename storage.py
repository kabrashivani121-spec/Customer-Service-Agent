from __future__ import annotations
import os
import sqlite3
from dataclasses import dataclass
from typing import Optional, Iterable, Any, Dict
from datetime import datetime

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  user_query TEXT NOT NULL,
  detected_language TEXT,
  prompt_variant TEXT NOT NULL,
  category TEXT,
  sentiment TEXT,
  response TEXT,
  latency_ms INTEGER
);

CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  rating INTEGER NOT NULL,             -- 1 = up, -1 = down
  comment TEXT,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_variant ON conversations(prompt_variant);
"""

def _utcnow() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

@dataclass
class DB:
    path: str

    def connect(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def insert_conversation(self, **fields: Any) -> int:
        fields.setdefault("created_at", _utcnow())
        cols = ", ".join(fields.keys())
        qs = ", ".join(["?"] * len(fields))
        with self.connect() as conn:
            cur = conn.execute(f"INSERT INTO conversations ({cols}) VALUES ({qs})", list(fields.values()))
            conn.commit()
            return int(cur.lastrowid)

    def insert_feedback(self, conversation_id: int, rating: int, comment: str | None = None) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO feedback (conversation_id, created_at, rating, comment) VALUES (?, ?, ?, ?)",
                (conversation_id, _utcnow(), rating, comment),
            )
            conn.commit()
            return int(cur.lastrowid)

    def fetch_conversations(self, limit: int = 500) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY datetime(created_at) DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def fetch_feedback_joined(self, limit: int = 500) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT f.*, c.user_query, c.response, c.prompt_variant
                FROM feedback f
                JOIN conversations c ON c.id = f.conversation_id
                ORDER BY datetime(f.created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
