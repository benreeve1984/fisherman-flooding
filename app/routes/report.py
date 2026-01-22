from fasthtml.common import *

from app.components.report_form import report_form, submission_result
from app.services.road_service import (
    check_rate_limit,
    add_observation,
    hash_ip,
)
from app.services.ea_api import get_live_conditions
from app.models.domain import RoadId, RoadStatus, Confidence


def register_routes(rt):
    """Register report submission routes."""

    @rt('/report/{road_id}', methods=['GET'])
    def report_get(road_id: str):
        """Display report form for a specific road."""
        # Validate road_id
        try:
            RoadId(road_id)
        except ValueError:
            return P("Invalid road", cls="error")

        return report_form(road_id)

    @rt('/report/{road_id}', methods=['POST'])
    def report_post(
        road_id: str,
        status: str,
        confidence: str,
        comment: str = "",
        request=None,
    ):
        """Submit a new road observation."""
        # Validate road_id
        try:
            validated_road = RoadId(road_id)
        except ValueError:
            return submission_result(
                success=False,
                message="Invalid road",
                road_id=road_id
            )

        # Get client IP and hash it
        client_ip = "unknown"
        if request:
            # Try to get real IP from X-Forwarded-For (Vercel proxy)
            forwarded = request.headers.get("x-forwarded-for", "")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
            else:
                client_ip = request.client.host if request.client else "unknown"

        ip_hash = hash_ip(client_ip)

        # Rate limiting check
        is_limited, remaining = check_rate_limit(ip_hash)
        if is_limited:
            return submission_result(
                success=False,
                message=f"Too many reports. Try again in {remaining} minutes.",
                road_id=road_id
            )

        # Validate status
        try:
            validated_status = RoadStatus(int(status))
        except (ValueError, TypeError):
            return submission_result(
                success=False,
                message="Invalid status value",
                road_id=road_id
            )

        # Validate confidence
        try:
            validated_confidence = Confidence(confidence)
        except ValueError:
            return submission_result(
                success=False,
                message="Invalid confidence value",
                road_id=road_id
            )

        # Truncate and sanitize comment
        clean_comment = comment[:280].strip() if comment else None

        # Get current environmental conditions for data curation
        conditions = get_live_conditions()
        river_level = conditions.river.value if conditions.river else None
        rainfall_24h = conditions.rainfall_24h
        rainfall_48h = conditions.rainfall_48h
        rainfall_72h = conditions.rainfall_72h

        # Save observation with environmental context
        observation_id = add_observation(
            road_id=validated_road,
            status=validated_status,
            confidence=validated_confidence,
            ip_hash=ip_hash,
            comment=clean_comment,
            river_level_m=river_level,
            rainfall_24h_mm=rainfall_24h,
            rainfall_48h_mm=rainfall_48h,
            rainfall_72h_mm=rainfall_72h,
        )

        if observation_id:
            return submission_result(
                success=True,
                message="Your report has been recorded. Thank you for helping the community!",
                road_id=road_id
            )
        else:
            return submission_result(
                success=False,
                message="Failed to save report. Please try again.",
                road_id=road_id
            )
