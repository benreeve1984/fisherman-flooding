import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import time

from app.config import (
    EA_BASE_URL,
    EA_THAME_BRIDGE_STATION_ID,
    EA_CACHE_TTL,
    EA_REQUEST_TIMEOUT,
    SHABBINGTON_LAT,
    SHABBINGTON_LON,
    RAINFALL_SEARCH_DIST_KM,
    RAINFALL_NUM_STATIONS,
)
from app.models.domain import RiverReading, RainfallTotal, LiveConditions

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory TTL cache for EA API responses."""

    def __init__(self, ttl: int = EA_CACHE_TTL):
        self._cache: dict = {}
        self._timestamps: dict = {}
        self._ttl = ttl

    def get(self, key: str):
        """Get value from cache if not expired."""
        if key in self._cache:
            if time.monotonic() - self._timestamps[key] < self._ttl:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None

    def set(self, key: str, value):
        """Set value in cache."""
        self._cache[key] = value
        self._timestamps[key] = time.monotonic()

    def get_stale(self, key: str):
        """Get value even if expired (for fallback)."""
        return self._cache.get(key)


# Global cache instance
_cache = SimpleCache()


class EAApiError(Exception):
    """Custom exception for EA API failures."""
    pass


def _fetch(endpoint: str, params: dict = None) -> dict:
    """Make HTTP request to EA API with error handling."""
    url = f"{EA_BASE_URL}{endpoint}"

    try:
        with httpx.Client(timeout=EA_REQUEST_TIMEOUT) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error(f"EA API timeout: {url}")
        raise EAApiError("EA API request timed out")
    except httpx.HTTPStatusError as e:
        logger.error(f"EA API HTTP error {e.response.status_code}: {url}")
        raise EAApiError(f"EA API returned {e.response.status_code}")
    except Exception as e:
        logger.error(f"EA API unexpected error: {e}")
        raise EAApiError("EA API unavailable")


def get_river_level(station_id: str = None) -> Optional[RiverReading]:
    """
    Fetch latest river level reading from Thame Bridge station.

    Returns cached data if available and fresh.
    """
    station_id = station_id or EA_THAME_BRIDGE_STATION_ID
    cache_key = f"river_{station_id}"

    # Check cache first
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        # Fetch latest reading
        data = _fetch(f"/id/stations/{station_id}/readings", {"latest": ""})

        if not data.get("items"):
            return None

        reading = data["items"][0]
        reading_time = datetime.fromisoformat(
            reading["dateTime"].replace("Z", "+00:00")
        )

        # Check if data is stale (> 1 hour old)
        age = datetime.now(timezone.utc) - reading_time
        is_stale = age > timedelta(hours=1)

        # Calculate trend from recent readings
        trend = _calculate_trend(station_id)

        result = RiverReading(
            station_id=station_id,
            station_name="Thame Bridge",
            value=reading["value"],
            unit="m",
            timestamp=reading_time,
            trend=trend,
            is_stale=is_stale,
        )

        _cache.set(cache_key, result)
        return result

    except EAApiError:
        # Try to return stale cached data on error
        stale = _cache.get_stale(cache_key)
        if stale:
            stale.is_stale = True
            return stale
        return None


def _calculate_trend(station_id: str) -> Optional[str]:
    """Calculate river level trend from recent readings."""
    try:
        since = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        data = _fetch(f"/id/stations/{station_id}/readings", {"since": since})

        if not data.get("items") or len(data["items"]) < 2:
            return None

        # Sort by time descending
        readings = sorted(
            data["items"],
            key=lambda x: x["dateTime"],
            reverse=True
        )

        latest = readings[0]["value"]
        previous = readings[min(1, len(readings) - 1)]["value"]
        delta = latest - previous

        if delta >= 0.02:
            return "rising"
        elif delta <= -0.02:
            return "falling"
        else:
            return "steady"

    except Exception as e:
        logger.warning(f"Could not calculate trend: {e}")
        return None


def get_rainfall_stations() -> list[str]:
    """
    Find nearest rainfall stations to Shabbington.

    Returns list of station IDs.
    """
    cache_key = "rainfall_stations"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        data = _fetch("/id/stations", {
            "parameter": "rainfall",
            "lat": SHABBINGTON_LAT,
            "long": SHABBINGTON_LON,
            "dist": RAINFALL_SEARCH_DIST_KM,
        })

        if not data.get("items"):
            return []

        # Extract station IDs (take first N)
        station_ids = []
        for item in data["items"][:RAINFALL_NUM_STATIONS]:
            # Station ID is in the @id URL, extract last segment
            station_url = item.get("@id", "")
            station_id = station_url.split("/")[-1]
            if station_id:
                station_ids.append(station_id)

        _cache.set(cache_key, station_ids)
        return station_ids

    except EAApiError:
        return _cache.get_stale(cache_key) or []


def get_rainfall_total(station_id: str) -> Optional[RainfallTotal]:
    """Fetch rainfall totals for a single station."""
    cache_key = f"rain_{station_id}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        since = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
        data = _fetch(f"/id/stations/{station_id}/readings", {"since": since})

        if not data.get("items"):
            return None

        now = datetime.now(timezone.utc)
        total_24h = 0.0
        total_48h = 0.0
        total_72h = 0.0
        last_time = None

        for reading in data["items"]:
            reading_time = datetime.fromisoformat(
                reading["dateTime"].replace("Z", "+00:00")
            )
            age = now - reading_time
            value = reading.get("value", 0)

            if value and value > 0:
                if age <= timedelta(hours=24):
                    total_24h += value
                if age <= timedelta(hours=48):
                    total_48h += value
                if age <= timedelta(hours=72):
                    total_72h += value

            if last_time is None or reading_time > last_time:
                last_time = reading_time

        result = RainfallTotal(
            station_id=station_id,
            total_24h=round(total_24h, 1),
            total_48h=round(total_48h, 1),
            total_72h=round(total_72h, 1),
            last_reading_time=last_time,
        )

        _cache.set(cache_key, result)
        return result

    except EAApiError:
        return _cache.get_stale(cache_key)


def get_aggregated_rainfall() -> tuple[Optional[float], Optional[float], Optional[float], str]:
    """
    Get aggregated rainfall from all nearby stations.

    Returns: (24h_total, 48h_total, 72h_total, data_quality)
    Uses median across stations for robustness.
    """
    station_ids = get_rainfall_stations()
    if not station_ids:
        return None, None, None, "missing"

    totals = []
    for station_id in station_ids:
        total = get_rainfall_total(station_id)
        if total:
            totals.append(total)

    if not totals:
        return None, None, None, "missing"

    # Use median of totals
    def median(values):
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        if n == 0:
            return None
        if n % 2 == 0:
            return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        return sorted_vals[n // 2]

    rain_24h = median([t.total_24h for t in totals])
    rain_48h = median([t.total_48h for t in totals])
    rain_72h = median([t.total_72h for t in totals])

    quality = "ok" if len(totals) == len(station_ids) else "partial"

    return rain_24h, rain_48h, rain_72h, quality


def get_live_conditions() -> LiveConditions:
    """Get all live conditions in one call."""
    river = get_river_level()
    rain_24h, rain_48h, rain_72h, rain_quality = get_aggregated_rainfall()

    return LiveConditions(
        river=river,
        rainfall_24h=rain_24h,
        rainfall_48h=rain_48h,
        rainfall_72h=rain_72h,
        rain_data_quality=rain_quality,
        generated_at_utc=datetime.now(timezone.utc),
    )
