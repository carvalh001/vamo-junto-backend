import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Connection pool
connection_pool = None


def init_db_pool():
    """Initialize database connection pool"""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.database_url,
            cursor_factory=RealDictCursor
        )
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Error initializing database pool: {e}")
        raise


def close_db_pool():
    """Close database connection pool"""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        logger.info("Database connection pool closed")


@contextmanager
def get_db_connection():
    """Get database connection from pool (context manager)"""
    if connection_pool is None:
        init_db_pool()
    
    conn = connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        connection_pool.putconn(conn)


@contextmanager
def get_db_cursor():
    """Get database cursor (context manager)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

