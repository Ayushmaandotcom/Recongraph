import hashlib
import json
import sqlite3
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class SecureAuditTrail:
    """
    A tamper-evident, cryptographically signed audit log.
    Each entry's hash includes the previous entry's hash, forming a chain.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT UNIQUE NOT NULL,
                tenant_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                hash TEXT NOT NULL
            )
        """)
        self.conn.commit()
        
    def _get_last_hash(self) -> str:
        cursor = self.conn.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row["hash"]
        return "GENESIS_HASH"
        
    def _compute_hash(self, entry_id: str, tenant_id: str, timestamp: str, event_type: str, payload_str: str, prev_hash: str) -> str:
        data = f"{entry_id}|{tenant_id}|{timestamp}|{event_type}|{payload_str}|{prev_hash}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def append(self, tenant_id: str, event_type: str, payload: Dict[str, Any]) -> str:
        """
        Appends an event to the audit trail and returns its entry ID.
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(payload, sort_keys=True)
        
        with self.conn:
            prev_hash = self._get_last_hash()
            current_hash = self._compute_hash(entry_id, tenant_id, timestamp, event_type, payload_str, prev_hash)
            
            self.conn.execute("""
                INSERT INTO audit_log (entry_id, tenant_id, timestamp, event_type, payload, previous_hash, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (entry_id, tenant_id, timestamp, event_type, payload_str, prev_hash, current_hash))
            
        return entry_id

    def verify_chain(self) -> bool:
        """
        Verifies the cryptographic integrity of the entire audit chain.
        Returns True if the chain is valid, False otherwise.
        """
        cursor = self.conn.execute("SELECT * FROM audit_log ORDER BY id ASC")
        rows = cursor.fetchall()
        
        expected_prev_hash = "GENESIS_HASH"
        
        for row in rows:
            if row["previous_hash"] != expected_prev_hash:
                return False
                
            computed = self._compute_hash(
                row["entry_id"],
                row["tenant_id"],
                row["timestamp"],
                row["event_type"],
                row["payload"],
                row["previous_hash"]
            )
            
            if computed != row["hash"]:
                return False
                
            expected_prev_hash = row["hash"]
            
        return True
        
    def tamper(self, entry_id: str, new_payload: Dict[str, Any]):
        """
        FOR TESTING ONLY: Simulates a malicious actor altering a record without updating hashes.
        """
        payload_str = json.dumps(new_payload, sort_keys=True)
        with self.conn:
            self.conn.execute("UPDATE audit_log SET payload = ? WHERE entry_id = ?", (payload_str, entry_id))
