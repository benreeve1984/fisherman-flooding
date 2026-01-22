from fasthtml.common import *
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastHTML app
app, rt = fast_app(
    live=True,  # Enable live reload in development
    pico=False,  # We load Pico CSS manually in layout
)

# Register routes
from app.routes import home, report, api

home.register_routes(rt)
report.register_routes(rt)
api.register_routes(rt)


# Serve static files
@rt('/public/{fname:path}')
def get(fname: str):
    return FileResponse(f'public/{fname}')


# Health check endpoint
@rt('/health')
def get():
    from app.database import check_db_connection
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected"
    }


# Initialize database on first request (for serverless)
_db_initialized = False


@rt('/api/init')
def get():
    """Initialize database schema (call once after deployment)."""
    global _db_initialized
    if not _db_initialized:
        try:
            from app.database import init_db
            init_db()
            _db_initialized = True
            return {"status": "initialized"}
        except Exception as e:
            logger.error(f"Database init failed: {e}")
            return {"status": "error", "message": str(e)}
    return {"status": "already_initialized"}


# Debug endpoint - remove in production
@rt('/api/debug/observations')
def get():
    """Debug: List all observations."""
    try:
        from app.database import get_db_cursor
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM observations ORDER BY timestamp_utc DESC LIMIT 20")
            rows = cur.fetchall()
            return {"count": len(rows), "observations": [dict(r) for r in rows]}
    except Exception as e:
        return {"error": str(e)}


# Run server
if __name__ == "__main__":
    serve()
