"""
Batch Embedding Generator
==========================
Run this script once to generate embeddings for all existing videos
that have been processed by the tagging pipeline but don't have
embeddings yet.

Usage:
    cd backend
    python build_embeddings.py
"""

import os
import sys
import logging

# Ensure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _get_pg_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "pak_journal_archive"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def get_videos_without_embeddings():
    """Find processed videos that have no embedding yet."""
    conn = _get_pg_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT v.id::text AS video_id, v.original_filename, v.category
        FROM videos v
        WHERE v.status = 'completed'
          AND v.id NOT IN (SELECT video_id FROM video_embeddings)
        ORDER BY v.upload_date
    """)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def get_video_metadata(video_id: str, conn):
    """Load summaries, topics, entities for a video."""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Summaries
    cur.execute("SELECT summary_text FROM summaries WHERE video_id::text = %s ORDER BY summary_id", (video_id,))
    summaries = [r["summary_text"] for r in cur.fetchall()]

    # Topics
    cur.execute("SELECT topic_keywords FROM topics WHERE video_id::text = %s", (video_id,))
    topic_kws = []
    for r in cur.fetchall():
        kws = r["topic_keywords"]
        if isinstance(kws, list):
            topic_kws.extend(str(k) for k in kws)

    # Entities
    cur.execute("SELECT entity_text FROM entities WHERE video_id::text = %s", (video_id,))
    entities = [r["entity_text"] for r in cur.fetchall()]

    # Category
    cur.execute("SELECT category FROM videos WHERE id::text = %s", (video_id,))
    row = cur.fetchone()
    category = row["category"] if row else ""

    cur.close()
    return summaries, topic_kws, entities, category or ""


def main():
    # Ensure the video_embeddings table exists
    conn = _get_pg_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS video_embeddings (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
            embedding BYTEA NOT NULL,
            embedding_input TEXT,
            model_name VARCHAR(100) DEFAULT 'LaBSE',
            dimensions INTEGER DEFAULT 768,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(video_id)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("video_embeddings table ensured")

    # Find videos to process
    videos = get_videos_without_embeddings()
    if not videos:
        logger.info("All videos already have embeddings. Nothing to do.")
        return

    logger.info(f"Found {len(videos)} videos without embeddings")

    from search.embeddings import (
        build_embedding_input, generate_embedding,
        save_embedding, init_faiss_index, unload_labse,
    )

    conn = _get_pg_conn()
    success = 0
    for i, v in enumerate(videos, 1):
        vid = v["video_id"]
        try:
            summaries, topics, entities, category = get_video_metadata(vid, conn)

            emb_input = build_embedding_input(summaries, topics, entities, category)
            if not emb_input:
                logger.warning(f"  [{i}/{len(videos)}] {vid} — empty input, skipping")
                continue

            emb_vec = generate_embedding(emb_input)
            save_embedding(vid, emb_vec, emb_input)
            success += 1
            logger.info(f"  [{i}/{len(videos)}] {vid} — done ({v['original_filename']})")

        except Exception as e:
            logger.error(f"  [{i}/{len(videos)}] {vid} — FAILED: {e}")

    conn.close()

    # Rebuild FAISS index
    logger.info("Rebuilding FAISS index...")
    count = init_faiss_index()
    logger.info(f"FAISS index rebuilt with {count} vectors")

    # Free model
    unload_labse()

    logger.info(f"Done. {success}/{len(videos)} videos embedded.")


if __name__ == "__main__":
    main()
