"""End-to-end ETL: DESTATIS workbook -> tidy records -> SQLite database.

Usage:
    python scripts/run_etl.py
    python scripts/run_etl.py --xlsx data/raw/grunddaten_2023.xlsx --db data/processed/hospitals.db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hospital_quality.build_db import build_database
from hospital_quality.parse import parse_workbook


def main(xlsx_path: str, db_path: str) -> None:
    """Parse the workbook and build the SQLite database."""
    if not Path(xlsx_path).exists():
        raise SystemExit(
            f"Source workbook not found: {xlsx_path}\n"
            "Download it first (see README) or pass --xlsx."
        )
    print(f"Parsing {xlsx_path} ...")
    records = parse_workbook(xlsx_path)
    print(f"  extracted {len(records):,} observations")

    numeric = sum(1 for r in records if r.value is not None)
    print(f"  {numeric:,} numeric, {len(records) - numeric:,} flagged (nil/unknown/etc.)")

    rows = build_database(records, db_path)
    print(f"Built {db_path} with {rows:,} rows.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the hospital SQLite DB from the DESTATIS workbook")
    parser.add_argument("--xlsx", default="data/raw/grunddaten_2023.xlsx")
    parser.add_argument("--db", default="data/processed/hospitals.db")
    args = parser.parse_args()
    main(args.xlsx, args.db)
