import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

from app.config import DATABASE_URL

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """
    Get a database connection.

    Uses a context manager to ensure connections are closed properly.
    For serverless, we create fresh connections per request.
    """
    conn = None
    try:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL not configured")

        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


@contextmanager
def get_db_cursor():
    """
    Get a database cursor with automatic commit/rollback.

    Usage:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM observations")
            rows = cur.fetchall()
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


def init_db():
    """Initialize database schema if it doesn't exist."""
    with get_db_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                timestamp_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                road_id VARCHAR(50) NOT NULL,
                status INTEGER NOT NULL CHECK (status BETWEEN 1 AND 5),
                confidence VARCHAR(20) NOT NULL,
                comment TEXT CHECK (char_length(comment) <= 280),
                ip_hash VARCHAR(64) NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_observations_road_time
            ON observations (road_id, timestamp_utc DESC);

            CREATE INDEX IF NOT EXISTS idx_observations_ip_time
            ON observations (ip_hash, timestamp_utc DESC);
        """)
        logger.info("Database schema initialized")


def check_db_connection():
    """Check if database connection is working."""
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
