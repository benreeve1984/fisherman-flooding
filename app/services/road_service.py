import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
from collections import defaultdict

from app.database import get_db_cursor
from app.config import (
    CONSENSUS_LOOKBACK_HOURS,
    CONFIDENCE_WEIGHTS,
    RATE_LIMIT_WINDOW,
    RATE_LIMIT_MAX,
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
    Check if IP has exceeded rate limit.

    Returns: (is_limited, minutes_until_reset)
    """
    try:
        with get_db_cursor() as cur:
            window_start = datetime.now(timezone.utc) - timedelta(seconds=RATE_LIMIT_WINDOW)

            cur.execute("""
                SELECT
                    COUNT(*) as count,
                    MIN(timestamp_utc) as oldest_submission
                FROM observations
                WHERE ip_hash = %s
                  AND timestamp_utc > %s
            """, (ip_hash, window_start))

            row = cur.fetchone()
            count = row["count"] if row else 0

            if count >= RATE_LIMIT_MAX:
                # Calculate minutes until oldest submission ages out
                if row and row["oldest_submission"]:
                    reset_time = row["oldest_submission"] + timedelta(seconds=RATE_LIMIT_WINDOW)
                    remaining = (reset_time - datetime.now(timezone.utc)).total_seconds() / 60
                    return True, max(1, int(remaining))
                return True, 60
            return False, 0
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # On error, allow the request but log it
        return False, 0


def add_observation(
    road_id: RoadId,
    status: RoadStatus,
    confidence: Confidence,
    ip_hash: str,
    comment: Optional[str] = None,
) -> Optional[str]:
    """
    Add a new road status observation.

    Returns the observation ID if successful, None on failure.
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO observations (road_id, status, confidence, comment, ip_hash)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (road_id.value, status.value, confidence.value, comment, ip_hash))

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
