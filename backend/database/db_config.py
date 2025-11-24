"""
Database configuration and connection management
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'pak_journal_archive'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Connection pool
connection_pool = None

def init_db_pool(minconn=1, maxconn=10):
    """Initialize database connection pool"""
    global connection_pool
    try:
        connection_pool = SimpleConnectionPool(minconn, maxconn, **DB_CONFIG)
        logger.info("✓ Database connection pool initialized")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize database pool: {e}")
        return False

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

@contextmanager
def get_db_cursor(commit=True):
    """Context manager for database cursor with dict results"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cursor.close()

def test_db_connection():
    """Test database connection"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"✓ Database connection successful: {version['version']}")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def close_db_pool():
    """Close all database connections"""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        logger.info("✓ Database connection pool closed")
