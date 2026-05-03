-- Part 5: BigQuery external tables with Hive partitioning.
--
-- Project and bucket values are filled in for this assignment run.
-- These tables read files uploaded by scripts/05_upload_to_gcs.py:
--   gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/csv/airnow_date=YYYY-MM-DD/data.csv
--   gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/jsonl/airnow_date=YYYY-MM-DD/data.jsonl
--   gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/parquet/airnow_date=YYYY-MM-DD/data.parquet
--
-- BigQuery reads airnow_date from the folder name. Queries with a WHERE clause
-- on airnow_date scan fewer files because BigQuery can prune other partitions.

CREATE SCHEMA IF NOT EXISTS `assignment3-495203.air_quality`;

-- Hourly observations: CSV, Hive-partitioned
CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.hourly_observations_csv_hive` (
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
WITH PARTITION COLUMNS (
  airnow_date DATE
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/csv/*'],
  skip_leading_rows = 1,
  hive_partition_uri_prefix = 'gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/csv',
  require_hive_partition_filter = FALSE
);

-- Hourly observations: newline-delimited JSON, Hive-partitioned
CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.hourly_observations_jsonl_hive` (
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
WITH PARTITION COLUMNS (
  airnow_date DATE
)
OPTIONS (
  format = 'NEWLINE_DELIMITED_JSON',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/jsonl/*'],
  hive_partition_uri_prefix = 'gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/jsonl',
  require_hive_partition_filter = FALSE
);

-- Hourly observations: Parquet, Hive-partitioned
CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.hourly_observations_parquet_hive`
WITH PARTITION COLUMNS (
  airnow_date DATE
)
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/parquet/*'],
  hive_partition_uri_prefix = 'gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/parquet',
  require_hive_partition_filter = FALSE
);

-- Example partition-pruned queries.
-- These scan less data than the non-partitioned wildcard tables because only
-- the folder airnow_date=2024-07-15 needs to be read.
SELECT COUNT(*) AS rows_on_july_15
FROM `assignment3-495203.air_quality.hourly_observations_csv_hive`
WHERE airnow_date = '2024-07-15';

SELECT parameter_name, AVG(value) AS avg_value, COUNT(*) AS observation_count
FROM `assignment3-495203.air_quality.hourly_observations_jsonl_hive`
WHERE airnow_date = '2024-07-15'
GROUP BY parameter_name
ORDER BY observation_count DESC;

SELECT parameter_name, AVG(value) AS avg_value, COUNT(*) AS observation_count
FROM `assignment3-495203.air_quality.hourly_observations_parquet_hive`
WHERE airnow_date = '2024-07-15'
GROUP BY parameter_name
ORDER BY observation_count DESC;
