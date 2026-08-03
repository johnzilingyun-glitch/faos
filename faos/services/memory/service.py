"""Agent Memory — cross-job memory system for AI analyst agents (Phase 8).

Enables agents to recall prior analyses and learn from past outcomes.
Uses SQLite for structured queries.
"""
import os
import sqlite3
import logging
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "faos_memory.db")


@dataclass
class MemoryEntry:
    """A single memory entry from a past analysis."""
    memory_id: str
    symbol: str
    role: str
    analysis_summary: str
    confidence: float
    created_at: str


@dataclass
class RecallResult:
    """Result of a memory recall query."""
    entries: List[MemoryEntry] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if not self.entries:
            return "无历史记忆"
        return f"召回 {len(self.entries)} 条相关记忆"


class MemoryService:
    """
    Cross-job memory system for AI analyst agents.
    
    Stores analysis outputs, enabling agents to:
    1. Recall prior analyses for the same stock
    2. Build on successful patterns
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_memory (
                        memory_id TEXT PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        role TEXT NOT NULL,
                        analysis_summary TEXT,
                        confidence REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_symbol_role ON agent_memory(symbol, role)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_created_at ON agent_memory(created_at DESC)")
                conn.commit()
            logger.info(f"SQLite Memory DB initialized at: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite Memory DB: {e}")

    def recall(self, symbol: str, role: str, limit: int = 3) -> RecallResult:
        """Recall relevant memories for a given stock and role."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT memory_id, symbol, role, analysis_summary, confidence, created_at 
                    FROM agent_memory 
                    WHERE symbol = ? AND role = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                    """,
                    (symbol, role, limit)
                )
                rows = cursor.fetchall()

            entries = [
                MemoryEntry(
                    memory_id=row["memory_id"],
                    symbol=row["symbol"],
                    role=row["role"],
                    analysis_summary=row["analysis_summary"] or "",
                    confidence=row["confidence"] or 0.5,
                    created_at=str(row["created_at"]) if row["created_at"] else "",
                )
                for row in rows
            ]
            return RecallResult(entries=entries)
        except Exception as e:
            logger.error(f"Failed to recall memory for {symbol}/{role}: {e}")
            return RecallResult()

    def store(
        self,
        symbol: str,
        role: str,
        analysis_summary: str,
        confidence: float = 0.5,
    ):
        """Store an analysis result for future recall."""
        import uuid
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO agent_memory (memory_id, symbol, role, analysis_summary, confidence, created_at) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        memory_id,
                        symbol,
                        role,
                        analysis_summary[:5000],  # truncate to prevent huge DB bloat
                        confidence,
                        datetime.now().isoformat(),
                    )
                )
                conn.commit()
            logger.info(f"Stored memory {memory_id} for {symbol}/{role}")
        except Exception as e:
            logger.error(f"Failed to store memory for {symbol}/{role}: {e}")


# Singleton
memory_service = MemoryService()
