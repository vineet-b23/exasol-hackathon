import sqlite3
import logging
from typing import Any, Dict
from .base import BaseDatabase

logger = logging.getLogger(__name__)

class SQLiteDatabase(BaseDatabase):
    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute(self, sql: str) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enables accessing columns by name
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(sql)
                rows = cursor.fetchall()
                
                # Convert sqlite3.Row objects to standard dictionaries
                data = [dict(row) for row in rows]
                
                return {
                    "status": "success",
                    "row_count": len(data),
                    "data": data
                }
        except sqlite3.Error as e:
            logger.error(f"Database execution error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": []
            }