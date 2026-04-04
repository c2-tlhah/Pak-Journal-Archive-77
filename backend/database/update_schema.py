import os
import psycopg2
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'pak_journal_archive'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def update_schema():
    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()
        
        # List of columns to add if they don't exist
        columns_to_add = [
            ("birth_date", "DATE"),
            ("country", "VARCHAR(100)"),
            ("phone_number", "VARCHAR(20)"),
            ("bio", "TEXT"),
            ("profile_picture", "VARCHAR(500)"),
            ("is_active", "BOOLEAN DEFAULT true"),
            ("last_login", "TIMESTAMP")
        ]

        for col_name, col_type in columns_to_add:
            try:
                logger.info(f"Attempting to add column {col_name}...")
                cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
                conn.commit()
                logger.info(f"[OK] Column {col_name} added or already exists")
            except Exception as e:
                conn.rollback()
                logger.error(f"Error adding column {col_name}: {e}")

        cur.close()
        conn.close()
        logger.info("Schema update completed successfully")

    except Exception as e:
        logger.error(f"Schema update failed: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Updating database schema...")
    update_schema()
