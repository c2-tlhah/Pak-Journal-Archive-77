"""
Migration: Add tagging pipeline tables
---------------------------------------
Run this once against an existing database to create the four new tables
required by tagging.py:  fusion_tags, entities, summaries, topics.

Usage:
    python migrate_tagging_tables.py
"""
import os
import sys
import psycopg2
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MIGRATION_SQL = """
-- Ensure the update_updated_at_column function exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- FUSION TAGS
CREATE TABLE IF NOT EXISTS fusion_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    segment_id INTEGER NOT NULL,
    segment_text TEXT,
    speaker_id VARCHAR(100),
    speaker_role VARCHAR(50),
    bertopic_tag VARCHAR(100),
    keyword_tag VARCHAR(100),
    vocab_tag VARCHAR(100),
    modules_agreed INTEGER DEFAULT 0,
    final_tags JSONB,
    low_confidence BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, segment_id)
);
CREATE INDEX IF NOT EXISTS idx_fusion_tags_video_id ON fusion_tags(video_id);
CREATE INDEX IF NOT EXISTS idx_fusion_tags_user_id ON fusion_tags(user_id);

-- ENTITIES
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_text VARCHAR(255) NOT NULL,
    entity_type VARCHAR(20) NOT NULL,
    mention_count INTEGER DEFAULT 1,
    mentioned_by_speakers JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, entity_text, entity_type)
);
CREATE INDEX IF NOT EXISTS idx_entities_video_id ON entities(video_id);
CREATE INDEX IF NOT EXISTS idx_entities_user_id ON entities(user_id);
CREATE INDEX IF NOT EXISTS idx_entities_entity_type ON entities(entity_type);

-- SUMMARIES
CREATE TABLE IF NOT EXISTS summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary_id INTEGER NOT NULL,
    summary_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, summary_id)
);
CREATE INDEX IF NOT EXISTS idx_summaries_video_id ON summaries(video_id);
CREATE INDEX IF NOT EXISTS idx_summaries_user_id ON summaries(user_id);

-- TOPICS
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL,
    topic_keywords JSONB,
    num_documents INTEGER DEFAULT 0,
    representative_sentences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, topic_id)
);
CREATE INDEX IF NOT EXISTS idx_topics_video_id ON topics(video_id);
CREATE INDEX IF NOT EXISTS idx_topics_user_id ON topics(user_id);

-- Triggers (DROP IF EXISTS to avoid duplicates)
DROP TRIGGER IF EXISTS update_fusion_tags_updated_at ON fusion_tags;
CREATE TRIGGER update_fusion_tags_updated_at BEFORE UPDATE ON fusion_tags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_entities_updated_at ON entities;
CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_summaries_updated_at ON summaries;
CREATE TRIGGER update_summaries_updated_at BEFORE UPDATE ON summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_topics_updated_at ON topics;
CREATE TRIGGER update_topics_updated_at BEFORE UPDATE ON topics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""


def run_migration():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "pak_journal_archive"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )
        cur = conn.cursor()
        cur.execute(MIGRATION_SQL)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Migration complete — fusion_tags, entities, summaries, topics tables created")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
