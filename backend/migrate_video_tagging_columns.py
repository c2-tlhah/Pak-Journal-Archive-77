"""
Migration: Add category, tags, frontend_payload columns to videos table.
Run once: python migrate_video_tagging_columns.py
"""
import os
import logging
import psycopg2
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "pak_journal_archive"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "postgres"),
)
cur = conn.cursor()

migrations = [
    ("category",         "ALTER TABLE videos ADD COLUMN IF NOT EXISTS category VARCHAR(100);"),
    ("tags",             "ALTER TABLE videos ADD COLUMN IF NOT EXISTS tags JSONB;"),
    ("frontend_payload", "ALTER TABLE videos ADD COLUMN IF NOT EXISTS frontend_payload JSONB;"),
]

for name, sql in migrations:
    try:
        cur.execute(sql)
        conn.commit()
        logger.info(f"[OK] Column '{name}' ensured on videos table")
    except Exception as e:
        conn.rollback()
        logger.error(f"[FAIL] Failed to add column '{name}': {e}")

cur.close()
conn.close()
logger.info("Migration complete.")
