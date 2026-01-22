from fasthtml.common import *
from monsterui.all import *

from app.components.river_card import river_card, format_time_ago
from app.components.rainfall_card import rainfall_card
from app.components.road_card import road_card, status_badge
from app.services.ea_api import get_river_level, get_aggregated_rainfall
from app.services.road_service import (
    get_consensus,
    get_recent_observations,
    get_24h_status_counts,
    get_status_change_info,
)
from app.models.domain import RoadId, CONFIDENCE_LABELS, STATUS_LABELS


def register_routes(rt):
    """Register HTMX partial update endpoints."""

    @rt('/api/river')
    def get():
        """HTMX partial: Refresh river level data."""
        reading = get_river_level()
        return river_card(reading)

    @rt('/api/rainfall')
    def get():
        """HTMX partial: Refresh rainfall data."""
        rain_24h, rain_48h, rain_72h, quality = get_aggregated_rainfall()
        return rainfall_card(rain_24h, rain_48h, rain_72h, quality)

    @rt('/api/road/{road_id}')
    def get(road_id: str):
        """HTMX partial: Refresh single road status card."""
        try:
            validated_road = RoadId(road_id)
        except ValueError:
            return P("Invalid road", cls="text-destructive")

        consensus = get_consensus(validated_road)
        status_counts = get_24h_status_counts(validated_road)
        status_change = get_status_change_info(validated_road)
        observations = get_recent_observations(validated_road, limit=5)

        return road_card(validated_road, consensus, status_counts, status_change, observations)

    @rt('/api/road/{road_id}/history')
    def get(road_id: str):
        """HTMX partial: Recent observation history for a road."""
        try:
            validated_road = RoadId(road_id)
        except ValueError:
            return P("Invalid road", cls="text-destructive")

        observations = get_recent_observations(validated_road, limit=5)

        if not observations:
            return Div(
                P("No recent reports", cls="text-muted-foreground text-sm text-center py-2"),
            )

        return Div(
            Ul(
                *[
                    Li(
                        DivFullySpaced(
                            DivLAligned(
                                status_badge(obs.status),
                                Span(
                                    CONFIDENCE_LABELS[obs.confidence],
                                    cls="text-muted-foreground text-sm"
                                ),
                                cls="gap-2"
                            ),
                            Span(format_time_ago(obs.timestamp_utc), cls="text-muted-foreground text-sm"),
                        ),
                        P(obs.comment, cls="text-sm text-muted-foreground italic mt-1") if obs.comment else None,
                        cls="py-2"
                    )
                    for obs in observations
                ],
                cls="divide-y"
            ),
            cls="history-content"
        )
