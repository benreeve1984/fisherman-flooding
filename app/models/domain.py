from enum import Enum, IntEnum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class RoadId(str, Enum):
    """Road identifiers for the two flood-prone entrances."""
    ICKFORD_ENTRANCE = "ICKFORD_ENTRANCE"
    FISHERMAN_THAME_ENTRANCE = "FISHERMAN_THAME_ENTRANCE"


class RoadStatus(IntEnum):
    """Road passability status, ordered by severity (1=best, 5=unknown)."""
    CLEAR = 1              # Passable in any car
    CAUTION = 2            # Small cars risky
    HIGH_CLEARANCE = 3     # 4x4 etc only
    CLOSED = 4             # Do not attempt
    UNKNOWN = 5            # No idea / not checked


class Confidence(str, Enum):
    """How the reporter knows the road status."""
    DROVE_IT = "DROVE_IT"    # Highest confidence
    SAW_IT = "SAW_IT"        # Medium confidence
    HEARD_IT = "HEARD_IT"    # Lowest confidence


# Human-readable labels
ROAD_LABELS = {
    RoadId.ICKFORD_ENTRANCE: "From Ickford",
    RoadId.FISHERMAN_THAME_ENTRANCE: "From Thame (Fisherman)",
}

ROAD_DESCRIPTIONS = {
    RoadId.ICKFORD_ENTRANCE: "Road from Ickford village",
    RoadId.FISHERMAN_THAME_ENTRANCE: "Road from Thame via Fisherman pub",
}

STATUS_LABELS = {
    RoadStatus.CLEAR: "Clear",
    RoadStatus.CAUTION: "Caution",
    RoadStatus.HIGH_CLEARANCE: "High Clearance Only",
    RoadStatus.CLOSED: "Closed",
    RoadStatus.UNKNOWN: "Unknown",
}

STATUS_DESCRIPTIONS = {
    RoadStatus.CLEAR: "Passable in any car",
    RoadStatus.CAUTION: "Drive carefully, small cars risky",
    RoadStatus.HIGH_CLEARANCE: "4x4 or high clearance only",
    RoadStatus.CLOSED: "Do not attempt",
    RoadStatus.UNKNOWN: "Status not known",
}

CONFIDENCE_LABELS = {
    Confidence.DROVE_IT: "I drove through it",
    Confidence.SAW_IT: "I saw it (walked/looked)",
    Confidence.HEARD_IT: "I heard from someone else",
}


@dataclass
class Observation:
    """A single road status observation submitted by a user."""
    id: str
    timestamp_utc: datetime
    road_id: RoadId
    status: RoadStatus
    confidence: Confidence
    comment: Optional[str]
    ip_hash: str


@dataclass
class ConsensusResult:
    """Aggregated consensus for a road's current status."""
    road_id: RoadId
    status: RoadStatus
    report_count: int
    last_report_time: Optional[datetime]


@dataclass
class RiverReading:
    """A river level reading from EA API."""
    station_id: str
    station_name: str
    value: float
    unit: str
    timestamp: datetime
    trend: Optional[str] = None  # "rising", "falling", "steady"
    is_stale: bool = False


@dataclass
class RainfallTotal:
    """Rainfall totals from an EA station."""
    station_id: str
    total_24h: float
    total_48h: float
    total_72h: float
    last_reading_time: Optional[datetime]
    unit: str = "mm"


@dataclass
class LiveConditions:
    """Combined live conditions for display."""
    river: Optional[RiverReading]
    rainfall_24h: Optional[float]
    rainfall_48h: Optional[float]
    rainfall_72h: Optional[float]
    rain_data_quality: str  # "ok", "partial", "missing"
    generated_at_utc: datetime
