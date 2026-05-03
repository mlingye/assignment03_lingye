"""Prepare raw AirNow files as CSV, JSONL, Parquet, and GeoParquet.

Examples:
    python scripts/02_prepare.py --start 2024-07-01 --end 2024-07-01
    python scripts/02_prepare.py --start 2024-07-01 --end 2024-07-31
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PREPARED_DIR = DATA_DIR / "prepared"
HOURLY_DIR = PREPARED_DIR / "hourly"
SITES_DIR = PREPARED_DIR / "sites"
AIRNOW_ENCODING = "latin1"

HOURLY_COLUMNS = [
    "valid_date",
    "valid_time",
    "aqsid",
    "site_name",
    "gmt_offset",
    "parameter_name",
    "reporting_units",
    "value",
    "data_source",
]


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid date. Use YYYY-MM-DD."
        ) from exc


def iter_dates(start: dt.date, end: dt.date):
    if end < start:
        raise ValueError("--end must be on or after --start")

    current = start
    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def raw_date_dir(date_str: str) -> Path:
    path = RAW_DIR / date_str
    if not path.exists():
        raise FileNotFoundError(
            f"Missing raw directory {path}. Run scripts/01_extract.py first."
        )
    return path


def normalize_valid_time(series: pd.Series) -> pd.Series:
    """Return BigQuery-friendly HH:MM:SS time strings where possible."""
    as_text = series.astype("string").str.strip()
    parsed = pd.to_datetime(as_text, errors="coerce").dt.strftime("%H:%M:%S")
    return parsed.fillna(as_text)


def read_hourly_for_date(date_str: str) -> pd.DataFrame:
    """Read and combine all available hourly files for one date."""
    date_dir = raw_date_dir(date_str)
    expected_files = [
        date_dir / f"HourlyData_{date_str.replace('-', '')}{hour:02d}.dat"
        for hour in range(24)
    ]
    missing_files = [path.name for path in expected_files if not path.exists()]
    if missing_files:
        raise FileNotFoundError(
            f"{date_str} is missing {len(missing_files)} hourly files, "
            f"including {missing_files[0]}. Re-run extraction for this date."
        )

    frames = []
    for path in expected_files:
        frame = pd.read_csv(
            path,
            sep="|",
            header=None,
            names=HOURLY_COLUMNS,
            encoding=AIRNOW_ENCODING,
            dtype={
                "valid_date": "string",
                "valid_time": "string",
                "aqsid": "string",
                "site_name": "string",
                "parameter_name": "string",
                "reporting_units": "string",
                "data_source": "string",
            },
        )
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    combined["valid_date"] = pd.to_datetime(
        combined["valid_date"], errors="coerce"
    ).dt.date.astype("string")
    combined["valid_date"] = combined["valid_date"].fillna(date_str)
    combined["valid_time"] = normalize_valid_time(combined["valid_time"])
    combined["gmt_offset"] = pd.to_numeric(combined["gmt_offset"], errors="coerce")
    combined["value"] = pd.to_numeric(combined["value"], errors="coerce")
    return combined


def prepare_hourly_outputs(date_str: str) -> None:
    """Write CSV, JSONL, and Parquet hourly files for one date."""
    HOURLY_DIR.mkdir(parents=True, exist_ok=True)
    output_base = HOURLY_DIR / date_str

    hourly = read_hourly_for_date(date_str)
    hourly.to_csv(output_base.with_suffix(".csv"), index=False)
    hourly.to_json(
        output_base.with_suffix(".jsonl"),
        orient="records",
        lines=True,
        date_format="iso",
    )
    hourly.to_parquet(output_base.with_suffix(".parquet"), index=False)
    print(f"  wrote hourly files for {date_str} ({len(hourly):,} rows)")


def prepare_hourly_csv(date_str: str) -> None:
    prepare_hourly_outputs(date_str)


def prepare_hourly_jsonl(date_str: str) -> None:
    prepare_hourly_outputs(date_str)


def prepare_hourly_parquet(date_str: str) -> None:
    prepare_hourly_outputs(date_str)


def find_site_locations_file(preferred_date: str | None = None) -> Path:
    """Find a Monitoring_Site_Locations_V2.dat file in data/raw."""
    if preferred_date:
        preferred_path = RAW_DIR / preferred_date / "Monitoring_Site_Locations_V2.dat"
        if preferred_path.exists():
            return preferred_path
        raise FileNotFoundError(
            f"Missing {preferred_path}. Run extraction for {preferred_date} first."
        )

    candidates = sorted(RAW_DIR.glob("*/Monitoring_Site_Locations_V2.dat"))
    if not candidates:
        raise FileNotFoundError(
            "No Monitoring_Site_Locations_V2.dat files found under data/raw/."
        )
    return candidates[-1]


def read_site_locations(preferred_date: str | None = None) -> pd.DataFrame:
    """Read, type, and deduplicate site locations to one row per AQSID."""
    path = find_site_locations_file(preferred_date)
    sites = pd.read_csv(path, sep="|", encoding=AIRNOW_ENCODING, dtype="string")
    sites.columns = [column.strip() for column in sites.columns]

    required = {"AQSID", "Latitude", "Longitude"}
    missing = required.difference(sites.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")

    sites["AQSID"] = sites["AQSID"].astype("string").str.strip()
    sites["Latitude"] = pd.to_numeric(sites["Latitude"], errors="coerce")
    sites["Longitude"] = pd.to_numeric(sites["Longitude"], errors="coerce")
    sites = sites.dropna(subset=["AQSID", "Latitude", "Longitude"])
    sites = sites.drop_duplicates(subset=["AQSID"], keep="first")
    return sites


def prepare_site_locations_outputs(preferred_date: str | None = None) -> None:
    """Write CSV, JSONL, and GeoParquet site location files."""
    SITES_DIR.mkdir(parents=True, exist_ok=True)
    sites = read_site_locations(preferred_date)

    sites.to_csv(SITES_DIR / "site_locations.csv", index=False)
    sites.to_json(
        SITES_DIR / "site_locations.jsonl",
        orient="records",
        lines=True,
        date_format="iso",
    )

    import geopandas as gpd

    geometry = gpd.points_from_xy(sites["Longitude"], sites["Latitude"])
    geo_sites = gpd.GeoDataFrame(sites, geometry=geometry, crs="EPSG:4326")
    geo_sites.to_parquet(SITES_DIR / "site_locations.geoparquet", index=False)
    print(f"  wrote site location files ({len(sites):,} deduplicated rows)")


def prepare_site_locations_csv() -> None:
    prepare_site_locations_outputs()


def prepare_site_locations_jsonl() -> None:
    prepare_site_locations_outputs()


def prepare_site_locations_geoparquet() -> None:
    prepare_site_locations_outputs()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare raw AirNow data as BigQuery-friendly files."
    )
    parser.add_argument("--start", type=parse_date, default=dt.date(2024, 7, 1))
    parser.add_argument("--end", type=parse_date, default=dt.date(2024, 7, 31))
    parser.add_argument(
        "--sites-date",
        type=parse_date,
        help="Use the site locations file from this raw date. Defaults to --end.",
    )
    parser.add_argument(
        "--skip-sites",
        action="store_true",
        help="Only prepare hourly files; do not write site location outputs.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    sites_date = args.sites_date or args.end
    if not args.skip_sites:
        print(f"Preparing site locations from {sites_date.isoformat()}")
        prepare_site_locations_outputs(sites_date.isoformat())

    for file_date in iter_dates(args.start, args.end):
        date_str = file_date.isoformat()
        print(f"Preparing hourly data for {date_str}")
        prepare_hourly_outputs(date_str)

    print("Done.")


if __name__ == "__main__":
    main()
