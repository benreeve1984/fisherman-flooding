from fasthtml.common import *
from monsterui.all import *
from typing import Optional


def rainfall_stat(period: str, value: Optional[float]):
    """Single rainfall statistic display."""
    if value is None:
        return Div(
            Span(period, cls="text-xs text-muted-foreground block"),
            Span("--", cls="text-lg font-bold tabular-nums"),
            Span("mm", cls="text-xs text-muted-foreground ml-0.5"),
            cls="text-center p-1.5 bg-muted/50 rounded-lg opacity-50"
        )

    return Div(
        Span(period, cls="text-xs text-muted-foreground block"),
        Span(f"{value:.1f}", cls="text-lg font-bold tabular-nums"),
        Span("mm", cls="text-xs text-muted-foreground ml-0.5"),
        cls="text-center p-1.5 bg-muted/50 rounded-lg"
    )


def rainfall_card(
    rain_24h: Optional[float],
    rain_48h: Optional[float],
    rain_72h: Optional[float],
    data_quality: str = "ok"
):
    """
    Compact rainfall totals from nearby stations.

    Shows 24/48/72 hour accumulations.
    Informational only - no automated alerts.
    """
    quality_cls = "text-muted-foreground"
    quality_text = "Nearby stations"

    if data_quality == "missing":
        quality_cls = "text-yellow-600"
        quality_text = "Data unavailable"
    elif data_quality == "partial":
        quality_cls = "text-yellow-600"
        quality_text = "Partial data"

    return Card(
        CardHeader(
            H4("Recent Rainfall", cls="text-sm font-semibold text-muted-foreground"),
            cls="pb-1"
        ),
        CardBody(
            Grid(
                rainfall_stat("24h", rain_24h),
                rainfall_stat("48h", rain_48h),
                rainfall_stat("72h", rain_72h),
                cols=3,
                cls="gap-2"
            ),
            cls="py-2"
        ),
        CardFooter(
            DivCentered(
                Small(quality_text, cls=quality_cls),
            ),
            cls="pt-1"
        ),
        hx_get="/api/rainfall",
        hx_trigger="every 300s",
        hx_swap="outerHTML",
        cls="rainfall-card",
        id="rainfall-card"
    )
