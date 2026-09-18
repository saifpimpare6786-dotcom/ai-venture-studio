import hashlib
import json
import sqlite3
import datetime
from typing import Dict, Any, Optional
from app.core.config import settings

class ContentHashCache:
    """
    ECC Content-Hash Cache Pattern (skills/content-hash-cache-pattern).
    Provides instant (<5ms) retrieval for deterministic report generation across identical project inputs.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._init_cache_table()

    def _init_cache_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_hash_cache (
                    hash_key TEXT PRIMARY KEY,
                    project_id TEXT,
                    report_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_hash ON content_hash_cache(hash_key)")
            conn.commit()

    @staticmethod
    def compute_hash(project_data: Dict[str, Any], report_type: str, version: str = "v2.2") -> str:
        """
        Computes a deterministic SHA-256 hash over normalized venture inputs.
        """
        key_fields = {
            "name": project_data.get("name", "").strip().lower(),
            "industry": project_data.get("industry", "").strip().lower(),
            "target_country": project_data.get("target_country", "").strip().lower(),
            "currency": project_data.get("currency", "USD").strip().upper(),
            "stage": project_data.get("stage", "idea").strip().lower(),
            "problem_statement": project_data.get("problem_statement", "").strip(),
            "solution_description": project_data.get("solution_description", "").strip(),
            "target_customers": project_data.get("target_customers", "").strip(),
            "revenue_model": project_data.get("revenue_model", "").strip(),
            "pricing_strategy": project_data.get("pricing_strategy", "").strip(),
            "budget": float(project_data.get("budget", 0)),
            "preferred_funding": float(project_data.get("preferred_funding", 0)),
            "team_size": int(project_data.get("team_size", 1)),
            "timeline": project_data.get("timeline", "12 months").strip(),
            "goals": sorted([g.strip() for g in project_data.get("goals", []) if g]),
            "report_type": report_type,
            "version": version
        }
        serialized = json.dumps(key_fields, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, hash_key: str) -> Optional[Dict[str, Any]]:
        # 1. Fast L1 Memory Cache Check
        if hash_key in self._memory_cache:
            return self._memory_cache[hash_key]

        # 2. L2 Persistent SQLite Cache Check
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT content FROM content_hash_cache WHERE hash_key = ?", (hash_key,))
            row = cursor.fetchone()
            if row:
                content = json.loads(row[0])
                self._memory_cache[hash_key] = content
                return content
        return None

    def set(self, hash_key: str, project_id: str, report_type: str, content: Dict[str, Any]):
        if not content or not isinstance(content, dict):
            return
        content_json = json.dumps(content)
        if "detail 1" in content_json or " - data" in content_json:
            return

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._memory_cache[hash_key] = content

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO content_hash_cache (hash_key, project_id, report_type, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(hash_key) DO UPDATE SET
                    content=excluded.content,
                    created_at=excluded.created_at
            """, (hash_key, project_id, report_type, content_json, now))
            conn.commit()

    def purge_corrupted(self) -> int:
        self._memory_cache.clear()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM content_hash_cache WHERE content LIKE '%detail 1%' OR content LIKE '% - % data%'")
            conn.commit()
            return cur.rowcount

content_cache = ContentHashCache()
