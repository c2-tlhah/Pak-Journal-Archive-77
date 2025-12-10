import psycopg2
from database.db_config import get_db_connection, init_db_pool
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_speaker_column():
    if not init_db_pool():
        logger.error("Failed to initialize DB pool")
        return

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='videos' AND column_name='speaker';
            """)
            
            if not cursor.fetchone():
                logger.info("Adding 'speaker' column to 'videos' table...")
                cursor.execute("ALTER TABLE videos ADD COLUMN speaker VARCHAR(100) DEFAULT 'Unknown Speaker';")
                # conn.commit() is handled by context manager
                logger.info("Successfully added 'speaker' column.")
            else:
                logger.info("'speaker' column already exists.")
            
            cursor.close()
        
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")

if __name__ == "__main__":
    add_speaker_column()
