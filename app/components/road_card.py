from fasthtml.common import *
from monsterui.all import *
from typing import Optional
from datetime import datetime

from app.models.domain import (
    RoadId,
    RoadStatus,
    ConsensusResult,
    ROAD_LABELS,
    STATUS_LABELS,
)
from app.components.river_card import format_time_ago


# Tailwind classes for status colors
STATUS_BG_CLASSES = {
    RoadStatus.CLEAR: "bg-green-100 dark:bg-green-900/30",
    RoadStatus.CAUTION: "bg-yellow-100 dark:bg-yellow-900/30",
    RoadStatus.HIGH_CLEARANCE: "bg-orange-100 dark:bg-orange-900/30",
    RoadStatus.CLOSED: "bg-red-100 dark:bg-red-900/30",
    RoadStatus.UNKNOWN: "bg-gray-100 dark:bg-gray-800",
}

STATUS_TEXT_CLASSES = {
    RoadStatus.CLEAR: "text-green-700 dark:text-green-300",
    RoadStatus.CAUTION: "text-yellow-700 dark:text-yellow-300",
    RoadStatus.HIGH_CLEARANCE: "text-orange-700 dark:text-orange-300",
    RoadStatus.CLOSED: "text-red-700 dark:text-red-300",
    RoadStatus.UNKNOWN: "text-gray-600 dark:text-gray-400",
}

STATUS_BORDER_CLASSES = {
    RoadStatus.CLEAR: "border-l-4 border-l-green-500",
    RoadStatus.CAUTION: "border-l-4 border-l-yellow-500",
    RoadStatus.HIGH_CLEARANCE: "border-l-4 border-l-orange-500",
    RoadStatus.CLOSED: "border-l-4 border-l-red-500",
    RoadStatus.UNKNOWN: "border-l-4 border-l-gray-400",
}

# For backwards compatibility with old CSS
STATUS_CLASSES = {
    RoadStatus.CLEAR: "status-clear",
    RoadStatus.CAUTION: "status-caution",
    RoadStatus.HIGH_CLEARANCE: "status-high-clearance",
    RoadStatus.CLOSED: "status-closed",
    RoadStatus.UNKNOWN: "status-unknown",
}


def status_badge(status: RoadStatus, large: bool = False):
    """Display a status badge with color coding."""
    if large:
        # Compact badge for card headers - don't let it get too big
        size_cls = "text-sm px-3 py-1.5 font-bold whitespace-nowrap"
    else:
        size_cls = "text-xs px-2 py-1 font-semibold"
    return Span(
        STATUS_LABELS[status],
        cls=f"inline-block rounded-lg {size_cls} {STATUS_BG_CLASSES[status]} {STATUS_TEXT_CLASSES[status]}"
    )


def summary_stat_text(status_counts: dict[RoadStatus, int]) -> Optional[str]:
    """Generate summary text from 24h status counts."""
    if not status_counts:
        return None

    # Find the most reported status
    total = sum(status_counts.values())
    if total == 0:
        return None

    # Highlight concerning statuses
    concerning = [RoadStatus.CLOSED, RoadStatus.HIGH_CLEARANCE, RoadStatus.CAUTION]
    for status in concerning:
        if status in status_counts and status_counts[status] > 0:
            count = status_counts[status]
            label = STATUS_LABELS[status].lower()
            return f"{count} report{'s' if count != 1 else ''} of '{label}' in last 24h"

    # Otherwise show clear reports
    if RoadStatus.CLEAR in status_counts:
        count = status_counts[RoadStatus.CLEAR]
        return f"{count} 'clear' report{'s' if count != 1 else ''} in last 24h"

    return f"{total} report{'s' if total != 1 else ''} in last 24h"


def status_change_banner(
    previous_status: RoadStatus,
    change_time: datetime
) -> Div:
    """Show a banner when status recently changed."""
    time_ago = format_time_ago(change_time)
    return Div(
        DivLAligned(
            Span("Status changed", cls="font-semibold"),
            Span(f"from {STATUS_LABELS[previous_status]} ({time_ago})", cls="text-muted-foreground"),
            cls="text-sm space-x-2"
        ),
        cls="bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200 px-3 py-2 rounded-md mb-3"
    )


def road_card(
    road_id: RoadId,
    consensus: Optional[ConsensusResult],
    status_counts: Optional[dict[RoadStatus, int]] = None,
    status_change: Optional[tuple[RoadStatus, datetime]] = None,
):
    """
    Full road status card with consensus display and report button.

    This is where alerts come from - community reports.
    Enhanced with summary stats and status change indicators.
    """
    road_label = ROAD_LABELS[road_id]
    status = consensus.status if consensus else RoadStatus.UNKNOWN
    border_class = STATUS_BORDER_CLASSES[status]

    # No recent reports state
    if consensus is None:
        return Card(
            CardHeader(
                DivFullySpaced(
                    H3(road_label, cls="text-lg font-semibold"),
                    status_badge(RoadStatus.UNKNOWN),
                ),
            ),
            CardBody(
                P("No recent reports - be the first!", cls="text-muted-foreground text-center py-4"),
            ),
            CardFooter(
                Button(
                    "Report Current Status",
                    hx_get=f"/report/{road_id.value}",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                    cls=ButtonT.primary + " w-full text-lg py-3",
                ),
            ),
            cls=f"road-card {border_class}",
            id=f"road-{road_id.value}"
        )

    time_ago = format_time_ago(consensus.last_report_time)
    summary = summary_stat_text(status_counts) if status_counts else None

    return Card(
        # Status change banner if applicable
        status_change_banner(status_change[0], status_change[1]) if status_change else None,

        CardHeader(
            DivFullySpaced(
                Div(
                    H3(road_label, cls="text-lg font-semibold"),
                    P(f"Last report: {time_ago}", cls="text-sm text-muted-foreground"),
                    cls="space-y-1"
                ),
                status_badge(consensus.status, large=True),
                cls="items-start"
            ),
        ),

        CardBody(
            # Summary stat
            Div(
                P(summary, cls="text-sm text-muted-foreground") if summary else None,
                cls="mb-2" if summary else ""
            ),
        ) if summary else None,

        CardFooter(
            DivFullySpaced(
                Button(
                    "Report Status",
                    hx_get=f"/report/{road_id.value}",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                    cls=ButtonT.primary + " flex-1 py-3",
                ),
                Button(
                    "History",
                    hx_get=f"/api/road/{road_id.value}/history",
                    hx_target=f"#history-{road_id.value}",
                    hx_swap="innerHTML",
                    cls=ButtonT.secondary + " py-3",
                ),
                cls="gap-2"
            ),
        ),
        Div(id=f"history-{road_id.value}", cls="px-4 pb-4"),
        hx_get=f"/api/road/{road_id.value}",
        hx_trigger="every 30s",
        hx_swap="outerHTML",
        cls=f"road-card {border_class}",
        id=f"road-{road_id.value}"
    )


def road_card_inner(road_id: RoadId, consensus: Optional[ConsensusResult]):
    """
    Inner content for HTMX partial updates.

    Returns just the status portion for refreshing.
    """
    if consensus is None:
        return Div(
            P("No recent reports", cls="text-muted-foreground"),
            status_badge(RoadStatus.UNKNOWN),
            cls="flex flex-col gap-2"
        )

    time_ago = format_time_ago(consensus.last_report_time)
    report_text = f"{consensus.report_count} report{'s' if consensus.report_count != 1 else ''}"

    return Div(
        status_badge(consensus.status),
        Div(
            Small(f"Last report: {time_ago}"),
            Small(f" ({report_text})", cls="text-muted-foreground"),
            cls="text-sm"
        ),
        cls="flex flex-col gap-2"
    )
