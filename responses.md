# Assignment 03 Responses

## Cloud Upload Information

Project ID: `assignment3-495203`

GCS bucket: `gs://musa5090-s26-lingye-assignment03-data`

Verified uploaded paths:

```text
gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/
gs://musa5090-s26-lingye-assignment03-data/air_quality/sites/
gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/csv/
gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/jsonl/
gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/parquet/
```

Normal upload contains 31 daily files for each hourly format (`.csv`, `.jsonl`, `.parquet`) plus the three site location files. Hive upload contains 31 date partitions for each hourly format under `airnow_date=YYYY-MM-DD`.

## Part 4: BigQuery External Tables

Run this SQL in BigQuery after confirming the uploaded GCS files.

```sql
CREATE SCHEMA IF NOT EXISTS `assignment3-495203.air_quality`;

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

CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.hourly_observations_parquet`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/hourly/2024-07-*.parquet']
);

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

CREATE OR REPLACE EXTERNAL TABLE `assignment3-495203.air_quality.site_locations_geoparquet`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://musa5090-s26-lingye-assignment03-data/air_quality/sites/site_locations.geoparquet']
);
```

### Validation Queries

```sql
SELECT COUNT(*) AS hourly_csv_rows
FROM `assignment3-495203.air_quality.hourly_observations_csv`;

SELECT COUNT(*) AS hourly_jsonl_rows
FROM `assignment3-495203.air_quality.hourly_observations_jsonl`;

SELECT COUNT(*) AS hourly_parquet_rows
FROM `assignment3-495203.air_quality.hourly_observations_parquet`;
```

BigQuery results:

| Table | Row Count |
|---|---:|
| `hourly_observations_csv` | 5,868,152 |
| `hourly_observations_jsonl` | 5,868,152 |
| `hourly_observations_parquet` | 5,868,152 |

### Cross-Table Join Query

```sql
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
```

BigQuery result for `2024-07-15`:

| State | Average PM2.5 | Observation Count |
|---|---:|---:|
| JK | 45.145833333333336 | 48 |
| NULL | 21.43062801932366 | 1,035 |
| OK | 18.70128205128207 | 312 |
| DS | 17.97916666666666 | 96 |
| AR | 17.05774647887324 | 71 |
| AZ | 15.4657505285412 | 473 |
| KS | 14.560732984293187 | 191 |
| SC | 14.523232323232321 | 198 |
| GA | 14.092364532019706 | 406 |
| TX | 14.036424474187369 | 1,046 |
| MO | 13.452777777777778 | 288 |
| NC | 13.058089668615985 | 513 |
| UT | 12.792651757188496 | 313 |
| ID | 12.636348122866895 | 586 |
| TN | 12.569187675070024 | 357 |
| DC | 12.318840579710143 | 69 |
| NJ | 11.65177304964539 | 282 |
| LA | 11.186590038314176 | 261 |
| KY | 11.126966292134824 | 356 |
| CT | 10.99685863874346 | 191 |
| NY | 10.80907407407408 | 540 |
| AL | 10.780139372822303 | 287 |
| ME | 10.553488372093023 | 215 |
| VA | 10.543750000000006 | 288 |
| MT | 9.942142857142862 | 420 |
| MA | 9.886879432624108 | 282 |
| MD | 9.78280542986425 | 221 |
| MN | 9.780821917808217 | 511 |
| PR | 9.695652173913043 | 23 |
| RI | 9.652777777777775 | 72 |
| PA | 9.536873508353208 | 838 |
| IL | 9.321611721611719 | 546 |
| IN | 9.243294117647057 | 425 |
| NH | 9.143055555555549 | 144 |
| MS | 8.982941176470584 | 170 |
| VT | 8.969444444444445 | 72 |
| SD | 8.790714285714284 | 140 |
| OH | 8.673076923076922 | 728 |
| DE | 8.559722222222229 | 144 |
| NM | 8.549429657794674 | 263 |
| IA | 8.548085106382977 | 235 |
| FL | 8.312677595628413 | 915 |
| WV | 8.063492063492063 | 63 |
| CA | 8.019934640522896 | 2,448 |
| NE | 7.880000000000001 | 25 |
| CO | 7.460060060060062 | 333 |
| CC | 7.4339961759082245 | 2,615 |
| WI | 6.914525139664802 | 358 |
| WY | 6.848181818181817 | 110 |
| OR | 6.811563876651986 | 908 |
| NV | 6.630210772833723 | 427 |
| MI | 5.978476190476188 | 525 |
| ND | 5.707368421052628 | 190 |
| MX | 5.612499999999999 | 24 |
| WA | 5.390729483282675 | 1,316 |
| HI | 3.475909090909089 | 220 |
| AK | 2.9635416666666683 | 96 |

## Part 5: Hive-Partitioned External Tables

```sql
CREATE SCHEMA IF NOT EXISTS `assignment3-495203.air_quality`;

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
```

```sql
SELECT COUNT(*) AS rows_on_july_15
FROM `assignment3-495203.air_quality.hourly_observations_parquet_hive`
WHERE airnow_date = '2024-07-15';
```

This scans less data because BigQuery can use the `airnow_date=2024-07-15` folder name to read only that daily partition instead of scanning every July file.

BigQuery Hive partition result:

| Query | Result |
|---|---:|
| CSV hive rows where `airnow_date = '2024-07-15'` | 189,799 |

JSONL and Parquet hive example query results for `airnow_date = '2024-07-15'`:

| Parameter | Average Value | Observation Count |
|---|---:|---:|
| PM2.5 | 10.234405780096967 | 32,387 |
| OZONE | 35.63147198599305 | 31,984 |
| TEMP | 26.679272594574854 | 16,442 |
| RWD | 207.46118299445482 | 12,984 |
| RWS | 4.044359613586784 | 12,836 |
| PM10 | 33.70906092355447 | 10,308 |
| WS | 2.4018699355911135 | 9,626 |
| NO2 | 5.338557619202744 | 9,207 |
| RHUM | 53.26912513318323 | 8,447 |
| WD | 206.19588156123828 | 7,430 |
| NO | 1.583288650580871 | 6,714 |
| SO2 | 0.7212859972573543 | 6,563 |
| BARPR | 1119.8930621140605 | 5,506 |
| NOX | 7.059919110212328 | 4,945 |
| SRAD | 284.71987000928453 | 4,308 |
| CO | 0.24151033008786513 | 4,211 |
| PRECIP | 0.15186915887850483 | 2,354 |
| PMC | 29.4258302583026 | 1,355 |
| NOY | 5.171802618328302 | 993 |
| BC | 0.5948691099476437 | 382 |
| NO2Y | 4.688674033149174 | 362 |
| UV-AETH | 40.589972144846776 | 359 |
| NH3 | 10.077083333333333 | 96 |

## Part 6: Analysis & Reflection

### 1. File Sizes

**Hourly data, single day (`2024-07-01`):** 189,404 prepared rows.

| Format | File Size |
|---|---:|
| CSV | 19,402,864 bytes (18.50 MiB) |
| JSONL | 44,265,896 bytes (42.22 MiB) |
| Parquet | 815,377 bytes (0.78 MiB) |

**Full July hourly prepared row count:** 5,868,152 rows across 31 daily files.

**Site locations:** 5,986 deduplicated site rows.

| Format | File Size |
|---|---:|
| CSV | 1,038,258 bytes (0.99 MiB) |
| JSONL | 2,960,707 bytes (2.82 MiB) |
| GeoParquet | 486,972 bytes (0.46 MiB) |

I expect Parquet to be the smallest or close to the smallest for the hourly observations because it stores data by column and compresses repeated values well. JSONL is likely larger because every row repeats the field names. CSV is usually more compact than JSONL, but it does not preserve types or geometry metadata the way Parquet/GeoParquet can.

### 2. Format Anatomy

CSV is a row-oriented text format. Each line is a record, and fields are separated by commas. It is easy to inspect and widely supported, but the file itself does not strongly store data types, so dates, numbers, and strings have to be interpreted by the tool reading the file.

Parquet is a columnar binary format. Instead of storing one full row after another, it stores values by column with metadata about names and types. That makes it less human-readable, but much better for analytical queries where I may only need a few columns out of a large dataset.

### 3. Choosing Formats for BigQuery

Parquet is usually preferred for BigQuery external tables because it is columnar and typed. If a query only needs `parameter_name`, `value`, and `valid_date`, BigQuery can avoid reading unnecessary columns. That can improve performance and reduce scanned bytes, which also reduces cost. CSV and JSONL are useful because they are portable and easy to debug, but BigQuery has to do more parsing work and generally scans them less efficiently.

### 4. Pipeline vs. Warehouse Joins

Keeping hourly observations and site locations as separate files avoids repeating site metadata on every observation row. That keeps the prepared hourly files smaller and lets me update or correct the site table separately. The trade-off is that every analysis needing location or state information has to do a join in BigQuery.

Joining during the prepare step would make queries simpler because each observation row would already include fields like latitude, longitude, state, and county. That might be better for a dashboard where the same joined view is used repeatedly. The cost is larger files, duplicated site metadata, and a transformation step that has to be rerun if the site fields or join logic change.

### 5. Choosing a Data Source

**a) Parent checking current air quality near a child's school:** I would use the AirNow API if the product only needs a small, current lookup near one school or one neighborhood. It is current and targeted. If I were building a larger app serving many schools, I would use AirNow hourly files in a pipeline so the app queries my own stored copy instead of repeatedly hitting the public API.

**b) Environmental justice advocate studying decade-long neighborhood air quality:** I would use AQS bulk downloads. This use case needs historical, quality-assured data over many years, and bulk files are a better fit than making many API requests with rate limits.

**c) School administrator needing automated morning AQI alerts:** I would use the AirNow API for a small alert system focused on one school or district because it needs current conditions every morning. For a district-wide product with many schools and repeated users, I would build from AirNow hourly files so the system is more reliable and does not depend on many live API calls.
