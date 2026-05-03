"""Upload prepared AirNow files to Google Cloud Storage.

Authenticate first with:
    gcloud auth application-default login

Examples:
    python scripts/03_upload_to_gcs.py --bucket musa5090-s26-lingye-data --project PROJECT_ID
    set GCS_BUCKET=musa5090-s26-lingye-data
    set GOOGLE_CLOUD_PROJECT=PROJECT_ID
    python scripts/03_upload_to_gcs.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from google.cloud import storage


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PREPARED_DIR = DATA_DIR / "prepared"
DEFAULT_BUCKET = "musa5090-s26-lingye-data"


def iter_prepared_uploads():
    """Yield local prepared files and their GCS object names."""
    hourly_dir = PREPARED_DIR / "hourly"
    sites_dir = PREPARED_DIR / "sites"

    for path in sorted(hourly_dir.glob("*")):
        if path.is_file() and path.suffix in {".csv", ".jsonl", ".parquet"}:
            yield path, f"air_quality/hourly/{path.name}"

    for path in sorted(sites_dir.glob("*")):
        if path.is_file() and path.suffix in {".csv", ".jsonl", ".geoparquet"}:
            yield path, f"air_quality/sites/{path.name}"


def upload_file(bucket, source_path: Path, destination_name: str, overwrite: bool) -> None:
    blob = bucket.blob(destination_name)
    if not overwrite and blob.exists():
        print(f"skip existing gs://{bucket.name}/{destination_name}")
        return

    blob.upload_from_filename(source_path)
    print(f"uploaded {source_path} -> gs://{bucket.name}/{destination_name}")


def upload_prepared_data(bucket_name: str, project_id: str | None, overwrite: bool) -> None:
    """Upload data/prepared files under the air_quality/ GCS prefix."""
    if not PREPARED_DIR.exists():
        raise FileNotFoundError(
            f"Missing {PREPARED_DIR}. Run scripts/02_prepare.py before uploading."
        )

    uploads = list(iter_prepared_uploads())
    if not uploads:
        raise FileNotFoundError(f"No prepared files found under {PREPARED_DIR}.")

    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)

    for source_path, destination_name in uploads:
        upload_file(bucket, source_path, destination_name, overwrite)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upload prepared AirNow files to Google Cloud Storage."
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
    upload_prepared_data(args.bucket, args.project, args.overwrite)
    print("Done.")


if __name__ == "__main__":
    main()
