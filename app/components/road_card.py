from fasthtml.common import *
from typing import Optional

from app.models.domain import (
    RoadId,
    RoadStatus,
    ConsensusResult,
    ROAD_LABELS,
    STATUS_LABELS,
)
from app.components.river_card import format_time_ago


# CSS class mappings for status colors
STATUS_CLASSES = {
    RoadStatus.CLEAR: "status-clear",
    RoadStatus.CAUTION: "status-caution",
    RoadStatus.HIGH_CLEARANCE: "status-high-clearance",
    RoadStatus.CLOSED: "status-closed",
    RoadStatus.UNKNOWN: "status-unknown",
}


def road_status_pill(status: RoadStatus):
    """Display a status pill with color coding."""
    return Span(
        STATUS_LABELS[status],
        cls=f"status-pill {STATUS_CLASSES[status]}"
    )


def road_card(road_id: RoadId, consensus: Optional[ConsensusResult]):
    """
    Full road status card with consensus display and report button.

    This is where alerts come from - community reports.
    """
    road_label = ROAD_LABELS[road_id]

    if consensus is None:
        # No recent reports
        return Article(
            Header(H3(road_label)),
            Div(
                P("No recent reports", cls="no-data"),
                road_status_pill(RoadStatus.UNKNOWN),
                cls="status-display"
            ),
            Footer(
                Button(
                    "Report Status",
                    hx_get=f"/report/{road_id.value}",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                    cls="report-button"
                ),
            ),
            cls="road-card",
            id=f"road-{road_id.value}"
        )

    time_ago = format_time_ago(consensus.last_report_time)
    report_text = f"{consensus.report_count} report{'s' if consensus.report_count != 1 else ''}"

    return Article(
        Header(H3(road_label)),
        Div(
            road_status_pill(consensus.status),
            Div(
                Small(f"Last report: {time_ago}"),
                Small(f" ({report_text})", cls="report-count"),
                cls="meta-row"
            ),
            cls="status-display",
            id=f"road-{road_id.value}-status"
        ),
        Footer(
            Button(
                "Report Status",
                hx_get=f"/report/{road_id.value}",
                hx_target="#modal-container",
                hx_swap="innerHTML",
                cls="report-button"
            ),
            Button(
                "History",
                hx_get=f"/api/road/{road_id.value}/history",
                hx_target=f"#history-{road_id.value}",
                hx_swap="innerHTML",
                cls="history-button outline"
            ),
        ),
        Div(id=f"history-{road_id.value}", cls="history-container"),
        hx_get=f"/api/road/{road_id.value}",
        hx_trigger="every 30s",
        hx_swap="outerHTML",
        cls=f"road-card {STATUS_CLASSES[consensus.status]}",
        id=f"road-{road_id.value}"
    )


def road_card_inner(road_id: RoadId, consensus: Optional[ConsensusResult]):
    """
    Inner content for HTMX partial updates.

    Returns just the status portion for refreshing.
    """
    if consensus is None:
        return Div(
            P("No recent reports", cls="no-data"),
            road_status_pill(RoadStatus.UNKNOWN),
            cls="status-display"
        )

    time_ago = format_time_ago(consensus.last_report_time)
    report_text = f"{consensus.report_count} report{'s' if consensus.report_count != 1 else ''}"

    return Div(
        road_status_pill(consensus.status),
        Div(
            Small(f"Last report: {time_ago}"),
            Small(f" ({report_text})", cls="report-count"),
            cls="meta-row"
        ),
        cls="status-display"
    )
