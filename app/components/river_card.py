from fasthtml.common import *
from datetime import datetime, timezone
from typing import Optional

from app.models.domain import RiverReading


def format_time_ago(dt: Optional[datetime]) -> str:
    """Format datetime as human-readable time ago string."""
    if dt is None:
        return "unknown"

    now = datetime.now(timezone.utc)
    # Ensure dt is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    delta = now - dt
    minutes = int(delta.total_seconds() / 60)

    if minutes < 1:
        return "just now"
    elif minutes < 60:
        return f"{minutes}m ago"
    elif minutes < 1440:
        hours = minutes // 60
        return f"{hours}h ago"
    else:
        days = minutes // 1440
        return f"{days}d ago"


def trend_icon(trend: Optional[str]) -> str:
    """Get icon for river trend."""
    if trend == "rising":
        return "^"  # Arrow up
    elif trend == "falling":
        return "v"  # Arrow down
    else:
        return "-"  # Steady


def river_card(reading: Optional[RiverReading]):
    """
    Displays current river level with trend indicator.

    Informational only - no automated alerts based on level.
    """
    if reading is None:
        return Article(
            Header(H3("River Thame")),
            Div(
                P("Unable to fetch river level data", cls="error-text"),
                P("Will retry automatically", cls="muted"),
                cls="error-state"
            ),
            hx_get="/api/river",
            hx_trigger="load delay:60s",
            hx_swap="outerHTML",
            cls="river-card"
        )

    time_ago = format_time_ago(reading.timestamp)
    trend = reading.trend or "steady"
    trend_label = trend.capitalize()

    return Article(
        Header(H3("River Thame")),
        Div(
            Div(
                Span(f"{reading.value:.2f}", cls="level-value"),
                Span("m", cls="level-unit"),
                cls="level-display"
            ),
            Div(
                Span(trend_icon(trend), cls=f"trend-icon trend-{trend}"),
                Span(trend_label, cls="trend-label"),
                cls="trend-display"
            ),
            cls="level-row"
        ),
        Footer(
            Small(f"Thame Bridge | {time_ago}"),
            Small(" (data delayed)", cls="stale-warning") if reading.is_stale else None,
        ),
        hx_get="/api/river",
        hx_trigger="every 60s",
        hx_swap="outerHTML",
        cls="river-card",
        id="river-card"
    )
