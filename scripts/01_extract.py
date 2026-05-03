"""Extract EPA AirNow hourly and monitoring site files.

Examples:
    python scripts/01_extract.py --start 2024-07-01 --end 2024-07-01
    python scripts/01_extract.py --start 2024-07-01 --end 2024-07-31
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import requests


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
BASE_URL = "https://s3-us-west-1.amazonaws.com/files.airnowtech.org/airnow"
TIMEOUT_SECONDS = 60


def parse_date(value: str) -> dt.date:
    """Parse a YYYY-MM-DD date string for CLI arguments."""
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid date. Use YYYY-MM-DD."
        ) from exc


def iter_dates(start: dt.date, end: dt.date):
    """Yield each date from start through end, inclusive."""
    if end < start:
        raise ValueError("--end must be on or after --start")

    current = start
    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def download_file(url: str, output_path: Path) -> bool:
    """Download one URL unless it already exists.

    Returns True when a new file was saved, and False when the file was skipped
    or could not be downloaded.
    """
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"  skip existing {output_path.name}")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".part")

    try:
        with requests.get(url, stream=True, timeout=TIMEOUT_SECONDS) as response:
            response.raise_for_status()
            with tmp_path.open("wb") as output_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output_file.write(chunk)
        tmp_path.replace(output_path)
        print(f"  saved {output_path.name}")
        return True
    except requests.RequestException as exc:
        if tmp_path.exists():
            tmp_path.unlink()
        print(f"  ERROR downloading {url}: {exc}")
        return False


def airnow_url(file_date: dt.date, filename: str) -> str:
    """Build the AirNow S3 URL for a dated file."""
    yyyymmdd = file_date.strftime("%Y%m%d")
    return f"{BASE_URL}/{file_date:%Y}/{yyyymmdd}/{filename}"


def download_data_for_date(date_str: str) -> None:
    """Download all AirNow raw files for one date into data/raw/YYYY-MM-DD/."""
    file_date = dt.date.fromisoformat(date_str)
    yyyymmdd = file_date.strftime("%Y%m%d")
    date_dir = RAW_DIR / file_date.isoformat()

    for hour in range(24):
        filename = f"HourlyData_{yyyymmdd}{hour:02d}.dat"
        download_file(airnow_url(file_date, filename), date_dir / filename)

    site_filename = "Monitoring_Site_Locations_V2.dat"
    download_file(airnow_url(file_date, site_filename), date_dir / site_filename)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download EPA AirNow hourly and monitoring site files."
    )
    parser.add_argument("--start", type=parse_date, default=dt.date(2024, 7, 1))
    parser.add_argument("--end", type=parse_date, default=dt.date(2024, 7, 31))
    return parser


def main() -> None:
    args = build_parser().parse_args()

    for file_date in iter_dates(args.start, args.end):
        print(f"Downloading AirNow files for {file_date.isoformat()}")
        download_data_for_date(file_date.isoformat())

    print("Done.")


if __name__ == "__main__":
    main()
