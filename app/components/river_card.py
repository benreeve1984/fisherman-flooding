from fasthtml.common import *
from monsterui.all import *
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


def trend_indicator(trend: Optional[str]):
    """Get visual indicator for river trend."""
    if trend == "rising":
        return Span(
            UkIcon("trending-up", cls="w-4 h-4"),
            "Rising",
            cls="inline-flex items-center gap-1 text-red-600 dark:text-red-400 text-sm font-medium"
        )
    elif trend == "falling":
        return Span(
            UkIcon("trending-down", cls="w-4 h-4"),
            "Falling",
            cls="inline-flex items-center gap-1 text-green-600 dark:text-green-400 text-sm font-medium"
        )
    else:
        return Span(
            UkIcon("minus", cls="w-4 h-4"),
            "Steady",
            cls="inline-flex items-center gap-1 text-muted-foreground text-sm font-medium"
        )


def river_card(reading: Optional[RiverReading]):
    """
    Compact river level display with trend indicator.

    Informational only - no automated alerts based on level.
    """
    if reading is None:
        return Card(
            CardHeader(
                H4("River Thame", cls="text-sm font-semibold text-muted-foreground"),
                cls="pb-1"
            ),
            CardBody(
                DivCentered(
                    P("Data unavailable", cls="text-muted-foreground text-sm"),
                ),
                cls="py-2"
            ),
            hx_get="/api/river",
            hx_trigger="load delay:60s",
            hx_swap="outerHTML",
            cls="river-card"
        )

    time_ago = format_time_ago(reading.timestamp)
    trend = reading.trend or "steady"

    return Card(
        CardHeader(
            DivFullySpaced(
                H4("River Thame", cls="text-sm font-semibold text-muted-foreground"),
                trend_indicator(trend),
            ),
            cls="pb-1"
        ),
        CardBody(
            DivCentered(
                Div(
                    Span(f"{reading.value:.2f}", cls="text-2xl font-bold tabular-nums"),
                    Span("m", cls="text-base text-muted-foreground ml-1"),
                    cls="flex items-baseline"
                ),
            ),
            cls="py-1"
        ),
        CardFooter(
            DivCentered(
                Small(
                    f"Thame Bridge | {time_ago}",
                    Span(" (delayed)", cls="text-yellow-600") if reading.is_stale else None,
                    cls="text-muted-foreground"
                ),
            ),
            cls="pt-1"
        ),
        hx_get="/api/river",
        hx_trigger="every 60s",
        hx_swap="outerHTML",
        cls="river-card",
        id="river-card"
    )
