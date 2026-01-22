from fasthtml.common import *
from monsterui.all import *

from app.components.layout import page_layout, page_header
from app.components.river_card import river_card
from app.components.rainfall_card import rainfall_card
from app.components.road_card import road_card
from app.services.ea_api import get_live_conditions
from app.services.road_service import (
    get_all_consensus,
    get_24h_status_counts,
    get_status_change_info,
    get_recent_observations,
)
from app.models.domain import RoadId


def register_routes(rt):
    """Register home page routes."""

    @rt('/')
    def get():
        """Main dashboard page."""
        # Get live conditions from EA API
        conditions = get_live_conditions()

        # Get current road consensus statuses
        road_statuses = get_all_consensus()

        # Get 24h stats for each road
        road_stats = {
            road_id: get_24h_status_counts(road_id)
            for road_id in RoadId
        }

        # Get status change info for each road
        status_changes = {
            road_id: get_status_change_info(road_id)
            for road_id in RoadId
        }

        # Get recent observations for each road
        road_history = {
            road_id: get_recent_observations(road_id, limit=5)
            for road_id in RoadId
        }

        return page_layout(
            "Flood Pulse - Shabbington",
            Main(
                Container(
                    page_header(),

                    # Road status section - FIRST (most important for drivers)
                    Section(
                        DivLAligned(
                            H2("Road Conditions", cls="text-lg font-semibold"),
                            cls="mb-1"
                        ),
                        P("Community-reported passability - tap to report", cls="text-xs text-muted-foreground mb-3"),
                        Div(
                            road_card(
                                RoadId.ICKFORD_ENTRANCE,
                                road_statuses[RoadId.ICKFORD_ENTRANCE],
                                road_stats[RoadId.ICKFORD_ENTRANCE],
                                status_changes[RoadId.ICKFORD_ENTRANCE],
                                road_history[RoadId.ICKFORD_ENTRANCE],
                            ),
                            road_card(
                                RoadId.FISHERMAN_THAME_ENTRANCE,
                                road_statuses[RoadId.FISHERMAN_THAME_ENTRANCE],
                                road_stats[RoadId.FISHERMAN_THAME_ENTRANCE],
                                status_changes[RoadId.FISHERMAN_THAME_ENTRANCE],
                                road_history[RoadId.FISHERMAN_THAME_ENTRANCE],
                            ),
                            cls="space-y-3"
                        ),
                        cls="mb-6"
                    ),

                    # Environmental data section - secondary info
                    Section(
                        H2("Local Conditions", cls="text-sm font-semibold mb-3 text-muted-foreground"),
                        Grid(
                            river_card(conditions.river),
                            rainfall_card(
                                conditions.rainfall_24h,
                                conditions.rainfall_48h,
                                conditions.rainfall_72h,
                                conditions.rain_data_quality,
                            ),
                            cols_sm=1,
                            cols_md=2,
                            cls="gap-3"
                        ),
                        # Future plans note
                        Div(
                            P(
                                "This app shares community-reported road conditions. "
                                "Once we gather sufficient data, we plan to add rules-based and model-based "
                                "estimates using River Thame levels, rainfall, and seasonal patterns.",
                                cls="text-xs text-muted-foreground mb-2"
                            ),
                            P(
                                "Suggestions, data sources, issues, or want to contribute? "
                                "Post in the ",
                                Strong("Shabby People WhatsApp group"),
                                " and I'll connect with you.",
                                cls="text-xs text-muted-foreground"
                            ),
                            cls="mt-4 p-3 bg-muted/30 rounded-lg"
                        ),
                        cls="mb-6"
                    ),

                    # Modal container for report forms
                    Div(id="modal-container"),

                    cls="px-4 py-2 max-w-2xl mx-auto"
                ),
            )
        )
