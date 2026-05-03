"""Upload prepared hourly files to GCS using Hive-partitioned paths.

This script reuses files already written by scripts/02_prepare.py. It does not
download or transform data.

Authenticate first with:
    gcloud auth application-default login

Example:
    python scripts/05_upload_to_gcs.py --bucket musa5090-s26-lingye-data --project PROJECT_ID
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from google.cloud import storage


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HOURLY_DIR = DATA_DIR / "prepared" / "hourly"
DEFAULT_BUCKET = "musa5090-s26-lingye-data"

EXTENSION_TO_FOLDER = {
    ".csv": ("csv", "data.csv"),
    ".jsonl": ("jsonl", "data.jsonl"),
    ".parquet": ("parquet", "data.parquet"),
}


def iter_hive_uploads():
    """Yield local hourly files and Hive-partitioned GCS object names."""
    for path in sorted(HOURLY_DIR.glob("*")):
        if not path.is_file() or path.suffix not in EXTENSION_TO_FOLDER:
            continue

        date_str = path.stem
        folder, filename = EXTENSION_TO_FOLDER[path.suffix]
        destination = (
            f"air_quality/hourly/{folder}/airnow_date={date_str}/{filename}"
        )
        yield path, destination


def upload_with_hive_partitioning(
    bucket_name: str, project_id: str | None, overwrite: bool
) -> None:
    """Upload prepared hourly data to GCS using Hive partition folders."""
    if not HOURLY_DIR.exists():
        raise FileNotFoundError(
            f"Missing {HOURLY_DIR}. Run scripts/02_prepare.py before uploading."
        )

    uploads = list(iter_hive_uploads())
    if not uploads:
        raise FileNotFoundError(f"No hourly prepared files found under {HOURLY_DIR}.")

    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)

    for source_path, destination_name in uploads:
        blob = bucket.blob(destination_name)
        if not overwrite and blob.exists():
            print(f"skip existing gs://{bucket.name}/{destination_name}")
            continue

        blob.upload_from_filename(source_path)
        print(f"uploaded {source_path} -> gs://{bucket.name}/{destination_name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upload AirNow hourly files to Hive-partitioned GCS paths."
    )
    parser.add_argument(
        "--bucket",
        default=os.getenv("GCS_BUCKET", DEFAULT_BUCKET),
        help="GCS bucket name. Defaults to GCS_BUCKET or musa5090-s26-lingye-data.",
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GOOGLE_CLOUD_PROJECT"),
        help="Google Cloud project ID. Defaults to GOOGLE_CLOUD_PROJECT.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite objects that already exist. By default they are skipped.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    upload_with_hive_partitioning(args.bucket, args.project, args.overwrite)
    print("Done.")


if __name__ == "__main__":
    main()
