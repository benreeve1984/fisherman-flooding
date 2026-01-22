-- Migration: Add environmental data columns to observations
-- Run this to add river level and rainfall data storage

-- Add columns for environmental conditions at time of report
ALTER TABLE observations
ADD COLUMN IF NOT EXISTS river_level_m DECIMAL(5,3),
ADD COLUMN IF NOT EXISTS rainfall_24h_mm DECIMAL(6,2),
ADD COLUMN IF NOT EXISTS rainfall_48h_mm DECIMAL(6,2),
ADD COLUMN IF NOT EXISTS rainfall_72h_mm DECIMAL(6,2);

-- Add comment explaining columns
COMMENT ON COLUMN observations.river_level_m IS 'River Thame level at Thame Bridge (metres) at time of report';
COMMENT ON COLUMN observations.rainfall_24h_mm IS '24-hour rainfall total (mm) from nearby stations at time of report';
COMMENT ON COLUMN observations.rainfall_48h_mm IS '48-hour rainfall total (mm) from nearby stations at time of report';
COMMENT ON COLUMN observations.rainfall_72h_mm IS '72-hour rainfall total (mm) from nearby stations at time of report';
