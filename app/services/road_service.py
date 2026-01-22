import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
from collections import defaultdict

from app.database import get_db_cursor
from app.config import (
    CONSENSUS_LOOKBACK_HOURS,
    CONFIDENCE_WEIGHTS,
    RATE_LIMIT_HOUR_MAX,
    RATE_LIMIT_DAY_MAX,
    IP_SALT,
)
from app.models.domain import (
    RoadId,
    RoadStatus,
    Confidence,
    Observation,
    ConsensusResult,
)

logger = logging.getLogger(__name__)


def hash_ip(ip_address: str) -> str:
    """Create a salted hash of an IP address for privacy."""
    salted = f"{ip_address}{IP_SALT}"
    return hashlib.sha256(salted.encode()).hexdigest()


def check_rate_limit(ip_hash: str) -> tuple[bool, int]:
    """
    Check if IP has exceeded rate limit (1/hour, 4/day).

    Returns: (is_limited, minutes_until_reset)
    """
    try:
        with get_db_cursor() as cur:
            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(hours=24)

            # Check hourly limit
            cur.execute("""
                SELECT COUNT(*) as count, MAX(timestamp_utc) as latest
                FROM observations
                WHERE ip_hash = %s AND timestamp_utc > %s
            """, (ip_hash, hour_ago))
            hour_row = cur.fetchone()
            hour_count = hour_row["count"] if hour_row else 0

            if hour_count >= RATE_LIMIT_HOUR_MAX:
                # Minutes until the hour window resets
                if hour_row and hour_row["latest"]:
                    reset_time = hour_row["latest"] + timedelta(hours=1)
                    remaining = (reset_time - now).total_seconds() / 60
                    return True, max(1, int(remaining))
                return True, 60

            # Check daily limit
            cur.execute("""
                SELECT COUNT(*) as count, MIN(timestamp_utc) as oldest
                FROM observations
                WHERE ip_hash = %s AND timestamp_utc > %s
            """, (ip_hash, day_ago))
            day_row = cur.fetchone()
            day_count = day_row["count"] if day_row else 0

            if day_count >= RATE_LIMIT_DAY_MAX:
                # Minutes until oldest submission ages out of 24h window
                if day_row and day_row["oldest"]:
                    reset_time = day_row["oldest"] + timedelta(hours=24)
                    remaining = (reset_time - now).total_seconds() / 60
                    return True, max(1, int(remaining))
                return True, 60

            return False, 0
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return False, 0


def add_observation(
    road_id: RoadId,
    status: RoadStatus,
    confidence: Confidence,
    ip_hash: str,
    comment: Optional[str] = None,
    river_level_m: Optional[float] = None,
    rainfall_24h_mm: Optional[float] = None,
    rainfall_48h_mm: Optional[float] = None,
    rainfall_72h_mm: Optional[float] = None,
) -> Optional[str]:
    """
    Add a new road status observation with environmental context.

    Returns the observation ID if successful, None on failure.
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO observations (
                    road_id, status, confidence, comment, ip_hash,
                    river_level_m, rainfall_24h_mm, rainfall_48h_mm, rainfall_72h_mm
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                road_id.value, status.value, confidence.value, comment, ip_hash,
                river_level_m, rainfall_24h_mm, rainfall_48h_mm, rainfall_72h_mm
            ))

            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"Failed to add observation: {e}")
        return None


def get_consensus(road_id: RoadId) -> Optional[ConsensusResult]:
    """
    Calculate consensus status for a road based on recent reports.

    Uses weighted voting by confidence level.
    """
    try:
        with get_db_cursor() as cur:
            lookback = datetime.now(timezone.utc) - timedelta(hours=CONSENSUS_LOOKBACK_HOURS)

            cur.execute("""
                SELECT status, confidence, timestamp_utc
                FROM observations
                WHERE road_id = %s
                  AND timestamp_utc > %s
                ORDER BY timestamp_utc DESC
            """, (road_id.value, lookback))

            rows = cur.fetchall()
            if not rows:
                return None

            # Calculate weighted votes for each status
            status_weights = defaultdict(float)
            for row in rows:
                status = row["status"]
                confidence = row["confidence"]
                weight = CONFIDENCE_WEIGHTS.get(confidence, 0.5)
                status_weights[status] += weight

            # Find status with highest weight
            consensus_status = max(status_weights.keys(), key=lambda s: status_weights[s])
            last_report_time = rows[0]["timestamp_utc"]

            return ConsensusResult(
                road_id=road_id,
                status=RoadStatus(consensus_status),
                report_count=len(rows),
                last_report_time=last_report_time,
            )
    except Exception as e:
        logger.error(f"Failed to get consensus: {e}")
        return None


def get_all_consensus() -> dict[RoadId, Optional[ConsensusResult]]:
    """Get consensus status for all roads."""
    return {
        RoadId.ICKFORD_ENTRANCE: get_consensus(RoadId.ICKFORD_ENTRANCE),
        RoadId.FISHERMAN_THAME_ENTRANCE: get_consensus(RoadId.FISHERMAN_THAME_ENTRANCE),
    }


def get_recent_observations(road_id: RoadId, limit: int = 10) -> list[Observation]:
    """Get recent observations for a road."""
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, timestamp_utc, road_id, status, confidence, comment, ip_hash
                FROM observations
                WHERE road_id = %s
                ORDER BY timestamp_utc DESC
                LIMIT %s
            """, (road_id.value, limit))

            rows = cur.fetchall()
            return [
                Observation(
                    id=str(row["id"]),
                    timestamp_utc=row["timestamp_utc"],
                    road_id=RoadId(row["road_id"]),
                    status=RoadStatus(row["status"]),
                    confidence=Confidence(row["confidence"]),
                    comment=row["comment"],
                    ip_hash=row["ip_hash"],
                )
                for row in rows
            ]
    except Exception as e:
        logger.error(f"Failed to get recent observations: {e}")
        return []


def get_24h_status_counts(road_id: RoadId) -> dict[RoadStatus, int]:
    """
    Get count of reports by status in the last 24 hours.

    Returns dict mapping status to count of reports.
    """
    try:
        with get_db_cursor() as cur:
            lookback = datetime.now(timezone.utc) - timedelta(hours=24)

            cur.execute("""
                SELECT status, COUNT(*) as count
                FROM observations
                WHERE road_id = %s
                  AND timestamp_utc > %s
                GROUP BY status
                ORDER BY count DESC
            """, (road_id.value, lookback))

            rows = cur.fetchall()
            return {RoadStatus(row["status"]): row["count"] for row in rows}
    except Exception as e:
        logger.error(f"Failed to get 24h status counts: {e}")
        return {}


def get_status_change_info(road_id: RoadId) -> Optional[tuple[RoadStatus, datetime]]:
    """
    Detect if the most recent report changed the consensus status.

    Returns (previous_status, change_time) if status changed recently,
    or None if no recent change detected.
    """
    try:
        with get_db_cursor() as cur:
            # Get two most recent reports
            cur.execute("""
                SELECT status, timestamp_utc
                FROM observations
                WHERE road_id = %s
                ORDER BY timestamp_utc DESC
                LIMIT 2
            """, (road_id.value,))

            rows = cur.fetchall()
            if len(rows) < 2:
                return None

            current_status = RoadStatus(rows[0]["status"])
            previous_status = RoadStatus(rows[1]["status"])

            if current_status != previous_status:
                # Status changed with the latest report
                return (previous_status, rows[0]["timestamp_utc"])

            return None
    except Exception as e:
        logger.error(f"Failed to get status change info: {e}")
        return None
