import sqlite3
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone

class FeedbackLoop:
    """
    Captures human corrections (Human-in-the-Loop) from the UI and logs them 
    as Gold Standard training examples for automated model retraining.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ml_feedback_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feedback_id TEXT UNIQUE NOT NULL,
                tenant_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                purchase_id TEXT NOT NULL,
                gst_id TEXT NOT NULL,
                is_match BOOLEAN NOT NULL,
                features TEXT,
                user_id TEXT NOT NULL
            )
        """)
        self.conn.commit()
        
    def log_correction(
        self, 
        tenant_id: str, 
        user_id: str, 
        purchase_id: str, 
        gst_id: str, 
        is_match: bool, 
        features: Dict[str, float]
    ) -> str:
        """
        Logs a user decision. If a user manually matches or rejects a pair,
        that pair becomes a training label for the Ranker.
        """
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        features_json = json.dumps(features)
        
        with self.conn:
            self.conn.execute("""
                INSERT INTO ml_feedback_log 
                (feedback_id, tenant_id, timestamp, purchase_id, gst_id, is_match, features, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (feedback_id, tenant_id, timestamp, purchase_id, gst_id, is_match, features_json, user_id))
            
        return feedback_id
        
    def get_training_data(self, since_date: str = None) -> List[Dict[str, Any]]:
        """
        Retrieves formatted training data for the LightGBM ranker.
        """
        query = "SELECT * FROM ml_feedback_log"
        params = []
        
        if since_date:
            query += " WHERE timestamp >= ?"
            params.append(since_date)
            
        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()
        
        training_data = []
        for row in rows:
            training_data.append({
                "feedback_id": row["feedback_id"],
                "tenant_id": row["tenant_id"],
                "purchase_id": row["purchase_id"],
                "gst_id": row["gst_id"],
                "label": 1 if row["is_match"] else 0,
                "features": json.loads(row["features"]) if row["features"] else {}
            })
            
        return training_data
