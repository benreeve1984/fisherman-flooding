from fasthtml.common import *

from app.components.river_card import river_card, format_time_ago
from app.components.rainfall_card import rainfall_card
from app.components.road_card import road_card
from app.services.ea_api import get_river_level, get_aggregated_rainfall
from app.services.road_service import get_consensus, get_recent_observations
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
            return P("Invalid road", cls="error")

        consensus = get_consensus(validated_road)
        return road_card(validated_road, consensus)

    @rt('/api/road/{road_id}/history')
    def get(road_id: str):
        """HTMX partial: Recent observation history for a road."""
        try:
            validated_road = RoadId(road_id)
        except ValueError:
            return P("Invalid road", cls="error")

        observations = get_recent_observations(validated_road, limit=5)

        if not observations:
            return Div(
                P("No recent reports", cls="no-data"),
                cls="history-list"
            )

        return Div(
            Ul(
                *[
                    Li(
                        Span(STATUS_LABELS[obs.status], cls=f"status-badge"),
                        Span(f" - {CONFIDENCE_LABELS[obs.confidence].lower()}", cls="confidence"),
                        Span(f" ({format_time_ago(obs.timestamp_utc)})", cls="time-ago"),
                        P(obs.comment, cls="comment") if obs.comment else None,
                    )
                    for obs in observations
                ],
                cls="history-list"
            ),
            cls="history-content"
        )
