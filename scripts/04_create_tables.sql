-- Part 4: BigQuery external tables for AirNow prepared files.
--
-- Project and bucket values are filled in for this assignment run.
-- Run this file in the BigQuery console or with the bq CLI.

CREATE SCHEMA IF NOT EXISTS `assignment3-495203.air_quality`;

-- Hourly observations: CSV
CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.hourly_observations_csv` (
  valid_date DATE,
  valid_time TIME,
  aqsid STRING,
  site_name STRING,
  gmt_offset FLOAT64,
  parameter_name STRING,
  reporting_units STRING,
  value FLOAT64,
  data_source STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/2024-07-*.csv'],
  skip_leading_rows = 1
);

-- Hourly observations: newline-delimited JSON
CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.hourly_observations_jsonl` (
  valid_date DATE,
  valid_time TIME,
  aqsid STRING,
  site_name STRING,
  gmt_offset FLOAT64,
  parameter_name STRING,
  reporting_units STRING,
  value FLOAT64,
  data_source STRING
)
OPTIONS (
  format = 'NEWLINE_DELIMITED_JSON',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/2024-07-*.jsonl']
);

-- Hourly observations: Parquet
CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.hourly_observations_parquet`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/2024-07-*.parquet']
);

-- Site locations: CSV
CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.site_locations_csv` (
  StationID STRING,
  AQSID STRING,
  FullAQSID STRING,
  Parameter STRING,
  MonitorType STRING,
  SiteCode STRING,
  SiteName STRING,
  Status STRING,
  AgencyID STRING,
  AgencyName STRING,
  EPARegion STRING,
  Latitude FLOAT64,
  Longitude FLOAT64,
  Elevation FLOAT64,
  GMTOffset STRING,
  CountryFIPS STRING,
  CBSA_ID STRING,
  CBSA_Name STRING,
  StateAQSCode STRING,
  StateAbbreviation STRING,
  CountyAQSCode STRING,
  CountyName STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/sites/site_locations.csv'],
  skip_leading_rows = 1
);

-- Site locations: newline-delimited JSON
CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.site_locations_jsonl` (
  StationID STRING,
  AQSID STRING,
  FullAQSID STRING,
  Parameter STRING,
  MonitorType STRING,
  SiteCode STRING,
  SiteName STRING,
  Status STRING,
  AgencyID STRING,
  AgencyName STRING,
  EPARegion STRING,
  Latitude FLOAT64,
  Longitude FLOAT64,
  Elevation FLOAT64,
  GMTOffset STRING,
  CountryFIPS STRING,
  CBSA_ID STRING,
  CBSA_Name STRING,
  StateAQSCode STRING,
  StateAbbreviation STRING,
  CountyAQSCode STRING,
  CountyName STRING
)
OPTIONS (
  format = 'NEWLINE_DELIMITED_JSON',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/sites/site_locations.jsonl']
);

-- Site locations: GeoParquet
CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.site_locations_geoparquet`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/sites/site_locations.geoparquet']
);

-- Validation: hourly table row counts should match across formats.
SELECT COUNT(*) AS hourly_csv_rows
FROM `assignment3-495203.air_quality.hourly_observations_csv`;

SELECT COUNT(*) AS hourly_jsonl_rows
FROM `assignment3-495203.air_quality.hourly_observations_jsonl`;

SELECT COUNT(*) AS hourly_parquet_rows
FROM `assignment3-495203.air_quality.hourly_observations_parquet`;

-- Join validation: average PM2.5 by state for one date.
-- This uses the Parquet hourly table because it is normally the best external
-- table format for repeated analytical queries.
SELECT
  sites.StateAbbreviation AS state_name,
  AVG(hourly.value) AS avg_pm25,
  COUNT(*) AS observation_count
FROM `assignment3-495203.air_quality.hourly_observations_parquet` AS hourly
JOIN `assignment3-495203.air_quality.site_locations_geoparquet` AS sites
  ON hourly.aqsid = CAST(sites.AQSID AS STRING)
WHERE DATE(hourly.valid_date) = DATE '2024-07-15'
  AND hourly.parameter_name = 'PM2.5'
  AND hourly.value IS NOT NULL
GROUP BY state_name
ORDER BY avg_pm25 DESC;
