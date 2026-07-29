import os
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("faos.history")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "faos_history.db")

class HistoryStorage:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # WAL allows concurrent readers with one writer — the watchlist
        # background thread and the API loop both touch this database.
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history_records (
                        id TEXT PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        chat_history TEXT,
                        followup_history TEXT,
                        report_content TEXT,
                        decision TEXT,
                        analysis_reports TEXT,
                        discussion TEXT,
                        market_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_symbol ON history_records(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_created_at ON history_records(created_at DESC)")
                conn.commit()
            logger.info(f"SQLite History DB initialized at: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite History DB: {e}")

    def save_record(self, record: Dict[str, Any]) -> bool:
        """Save or replace a history record in SQLite."""
        try:
            rec_id = str(record.get("id") or "")
            symbol = str(record.get("symbol") or "Asset")
            timestamp = str(record.get("timestamp") or "")

            chat_history = json.dumps(record.get("chatHistory") or [], ensure_ascii=False)
            followup_history = json.dumps(record.get("followUpHistory") or [], ensure_ascii=False)
            report_content = record.get("reportContent") or ""
            decision = json.dumps(record.get("decision") or {}, ensure_ascii=False)
            analysis_reports = json.dumps(record.get("analysisReports") or {}, ensure_ascii=False)
            discussion = json.dumps(record.get("discussion") or {}, ensure_ascii=False)
            market_data = json.dumps(record.get("marketData") or {}, ensure_ascii=False)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO history_records (
                        id, symbol, timestamp, chat_history, followup_history,
                        report_content, decision, analysis_reports, discussion, market_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rec_id, symbol, timestamp, chat_history, followup_history,
                    report_content, decision, analysis_reports, discussion, market_data
                ))
                conn.commit()
            logger.info(f"Saved history record {rec_id} for symbol {symbol} to SQLite")
            return True
        except Exception as e:
            logger.error(f"Error saving history record to SQLite: {e}")
            return False

    def list_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all history records from SQLite."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, symbol, timestamp, chat_history, followup_history,
                           report_content, decision, analysis_reports, discussion, market_data
                    FROM history_records
                    ORDER BY rowid DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                
                records = []
                for row in rows:
                    records.append({
                        "id": row["id"],
                        "symbol": row["symbol"],
                        "timestamp": row["timestamp"],
                        "chatHistory": json.loads(row["chat_history"]) if row["chat_history"] else [],
                        "followUpHistory": json.loads(row["followup_history"]) if row["followup_history"] else [],
                        "reportContent": row["report_content"],
                        "decision": json.loads(row["decision"]) if row["decision"] else None,
                        "analysisReports": json.loads(row["analysis_reports"]) if row["analysis_reports"] else None,
                        "discussion": json.loads(row["discussion"]) if row["discussion"] else None,
                        "marketData": json.loads(row["market_data"]) if row["market_data"] else None,
                    })
                return records
        except Exception as e:
            logger.error(f"Error listing history records from SQLite: {e}")
            return []

    def delete_record(self, record_id: str) -> bool:
        """Delete a single history record by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history_records WHERE id = ?", (record_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting history record {record_id} from SQLite: {e}")
            return False

    def clear_all(self) -> bool:
        """Clear all history records."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history_records")
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error clearing history records in SQLite: {e}")
            return False

# Global storage instance
history_storage = HistoryStorage()
