-- Flood Pulse Database Schema
-- Run this once to initialize the database

-- Observations table for road status reports
CREATE TABLE IF NOT EXISTS observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    road_id VARCHAR(50) NOT NULL,
    status INTEGER NOT NULL CHECK (status BETWEEN 1 AND 5),
    confidence VARCHAR(20) NOT NULL,
    comment TEXT CHECK (char_length(comment) <= 280),
    ip_hash VARCHAR(64) NOT NULL
);

-- Index for fetching recent observations by road (most common query)
CREATE INDEX IF NOT EXISTS idx_observations_road_time
ON observations (road_id, timestamp_utc DESC);

-- Index for rate limiting queries by IP hash
CREATE INDEX IF NOT EXISTS idx_observations_ip_time
ON observations (ip_hash, timestamp_utc DESC);

-- Road status values:
-- 1 = CLEAR (passable in any car)
-- 2 = CAUTION (small cars risky)
-- 3 = HIGH_CLEARANCE (4x4 etc only)
-- 4 = CLOSED (do not attempt)
-- 5 = UNKNOWN (not checked)

-- Confidence values:
-- DROVE_IT (highest weight: 1.0)
-- SAW_IT (medium weight: 0.8)
-- HEARD_IT (lowest weight: 0.3)
