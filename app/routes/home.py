from fasthtml.common import *

from app.components.layout import page_layout, page_header
from app.components.river_card import river_card
from app.components.rainfall_card import rainfall_card
from app.components.road_card import road_card
from app.services.ea_api import get_live_conditions
from app.services.road_service import get_all_consensus
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

        return page_layout(
            "Flood Pulse - Shabbington",
            Main(
                page_header(),

                # River level section
                Section(
                    H2("River Level"),
                    river_card(conditions.river),
                    cls="section"
                ),

                # Rainfall section
                Section(
                    H2("Recent Rainfall"),
                    rainfall_card(
                        conditions.rainfall_24h,
                        conditions.rainfall_48h,
                        conditions.rainfall_72h,
                        conditions.rain_data_quality,
                    ),
                    cls="section"
                ),

                # Road status section
                Section(
                    H2("Road Conditions"),
                    P("Community-reported passability", cls="section-subtitle"),
                    road_card(RoadId.ICKFORD_ENTRANCE, road_statuses[RoadId.ICKFORD_ENTRANCE]),
                    road_card(RoadId.FISHERMAN_THAME_ENTRANCE, road_statuses[RoadId.FISHERMAN_THAME_ENTRANCE]),
                    cls="section"
                ),

                # Modal container for report forms
                Div(id="modal-container"),

                cls="container"
            )
        )
