import sys
import os
sys.path.insert(0, 'd:/ECC/ECC/AI Venture Studio/backend')
import sqlite3
from app.core.config import settings

def purge():
    db_path = settings.SQLITE_DB_PATH
    print(f"Purging corrupted cache & reports from {db_path}...")
    with sqlite3.connect(db_path) as conn:
        c1 = conn.execute("DELETE FROM content_hash_cache WHERE content LIKE '%detail 1%' OR content LIKE '% - % data%'")
        print(f"Deleted {c1.rowcount} corrupted cache rows.")
        c2 = conn.execute("DELETE FROM reports WHERE content LIKE '%detail 1%' OR content LIKE '% - % data%'")
        print(f"Deleted {c2.rowcount} corrupted report rows.")
        conn.commit()

if __name__ == "__main__":
    purge()
