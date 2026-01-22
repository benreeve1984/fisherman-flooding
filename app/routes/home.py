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

        return page_layout(
            "Flood Pulse - Shabbington",
            Main(
                Container(
                    page_header(),

                    # Road status section - FIRST (most important for drivers)
                    Section(
                        DivLAligned(
                            H2("Road Conditions", cls="text-xl font-semibold"),
                            cls="mb-2"
                        ),
                        P("Community-reported passability - tap to report", cls="text-sm text-muted-foreground mb-4"),
                        Div(
                            road_card(
                                RoadId.ICKFORD_ENTRANCE,
                                road_statuses[RoadId.ICKFORD_ENTRANCE],
                                road_stats[RoadId.ICKFORD_ENTRANCE],
                                status_changes[RoadId.ICKFORD_ENTRANCE],
                            ),
                            road_card(
                                RoadId.FISHERMAN_THAME_ENTRANCE,
                                road_statuses[RoadId.FISHERMAN_THAME_ENTRANCE],
                                road_stats[RoadId.FISHERMAN_THAME_ENTRANCE],
                                status_changes[RoadId.FISHERMAN_THAME_ENTRANCE],
                            ),
                            cls="space-y-4"
                        ),
                        cls="mb-8"
                    ),

                    # Environmental data section - secondary info
                    Section(
                        H2("Local Conditions", cls="text-lg font-semibold mb-4 text-muted-foreground"),
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
                            cls="gap-4"
                        ),
                        cls="mb-8"
                    ),

                    # Modal container for report forms
                    Div(id="modal-container"),

                    cls="px-4 py-2 max-w-2xl mx-auto"
                ),
            )
        )
