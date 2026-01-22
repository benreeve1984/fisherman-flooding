import os
from dotenv import load_dotenv

load_dotenv()

# Village location
SHABBINGTON_LAT = 51.7485
SHABBINGTON_LON = -1.0030

# Environment Agency API
EA_BASE_URL = "https://environment.data.gov.uk/flood-monitoring"
EA_THAME_BRIDGE_STATION_ID = "1961TH"  # Thame Bridge on River Thame (verified)
EA_CACHE_TTL = 300  # 5 minutes
EA_REQUEST_TIMEOUT = 10  # seconds

# Rainfall settings
RAINFALL_SEARCH_DIST_KM = 15
RAINFALL_NUM_STATIONS = 3
RAINFALL_WINDOWS_HOURS = [24, 48, 72]

# Consensus calculation
CONSENSUS_LOOKBACK_HOURS = 8
CONFIDENCE_WEIGHTS = {
    "DROVE_IT": 1.0,
    "SAW_IT": 0.8,
    "HEARD_IT": 0.3,
}

# Rate limiting
RATE_LIMIT_HOUR_MAX = 2  # max reports per hour per IP (one per road)
RATE_LIMIT_DAY_MAX = 6   # max reports per 24 hours per IP

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", os.environ.get("POSTGRES_URL", ""))

# Security
IP_SALT = os.environ.get("IP_SALT", "change-this-in-production")
