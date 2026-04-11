"""Quick migration to create video_embeddings table."""
import psycopg2, os

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "pak_journal_archive"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "postgres"),
)
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
cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_video_embeddings_video_id
    ON video_embeddings(video_id)
""")
conn.commit()
cur.close()
conn.close()
print("video_embeddings table created successfully")
