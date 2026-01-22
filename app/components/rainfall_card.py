from fasthtml.common import *
from typing import Optional


def rainfall_stat(period: str, value: Optional[float]):
    """Single rainfall statistic display."""
    if value is None:
        return Div(
            Span(period, cls="period-label"),
            Span("--", cls="rainfall-value"),
            Span("mm", cls="rainfall-unit"),
            cls="rainfall-stat missing"
        )

    return Div(
        Span(period, cls="period-label"),
        Span(f"{value:.1f}", cls="rainfall-value"),
        Span("mm", cls="rainfall-unit"),
        cls="rainfall-stat"
    )


def rainfall_card(
    rain_24h: Optional[float],
    rain_48h: Optional[float],
    rain_72h: Optional[float],
    data_quality: str = "ok"
):
    """
    Displays rainfall totals aggregated from nearby stations.

    Shows 24/48/72 hour accumulations.
    Informational only - no automated alerts.
    """
    quality_note = None
    if data_quality == "missing":
        quality_note = Small("Rainfall data unavailable", cls="data-quality missing")
    elif data_quality == "partial":
        quality_note = Small("Some stations unavailable", cls="data-quality partial")

    return Article(
        Header(H3("Recent Rainfall")),
        Div(
            rainfall_stat("24h", rain_24h),
            rainfall_stat("48h", rain_48h),
            rainfall_stat("72h", rain_72h),
            cls="rainfall-grid"
        ),
        Footer(
            quality_note if quality_note else Small("From nearby stations"),
        ),
        hx_get="/api/rainfall",
        hx_trigger="every 300s",
        hx_swap="outerHTML",
        cls="rainfall-card",
        id="rainfall-card"
    )
