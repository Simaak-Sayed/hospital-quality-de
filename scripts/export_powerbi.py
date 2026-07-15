"""Export Power BI-ready datasets from the processed analysis outputs.

Power BI imports flat, well-typed tables most easily. This script produces:

* ``powerbi/state_indicators_2023.csv`` - one row per federal state combining
  capacity and staffing, ready to drop straight onto a map and bar charts.
* ``powerbi/national_trends.csv`` - the yearly national series for the line chart.

Run after ``scripts/run_analysis.py``:
    python scripts/export_powerbi.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
POWERBI = ROOT / "powerbi"


def main() -> None:
    """Merge the processed CSVs into Power BI-friendly flat tables."""
    capacity_path = PROCESSED / "capacity_by_state_2023.csv"
    staffing_path = PROCESSED / "staffing_by_state_2023.csv"
    national_path = PROCESSED / "national_trends.csv"
    if not capacity_path.exists():
        raise SystemExit("Processed CSVs not found. Run scripts/run_analysis.py first.")

    capacity = pd.read_csv(capacity_path)
    staffing = pd.read_csv(staffing_path)

    # One denormalised state table: capacity + staffing joined on the state key.
    merged = capacity.merge(
        staffing[["name_en", "fte_total", "fte_physicians", "fte_nursing",
                  "nursing_fte_per_bed", "beds_per_nursing_fte"]],
        on="name_en",
        how="left",
    )
    merged = merged.rename(
        columns={
            "code": "State code",
            "name_en": "State",
            "population": "Population",
            "beds": "Beds",
            "icu_beds": "ICU beds",
            "utilization_pct": "Bed utilisation %",
            "beds_per_100k": "Beds per 100k",
            "icu_beds_per_100k": "ICU beds per 100k",
            "fte_total": "Staff FTE (total)",
            "fte_physicians": "Physician FTE",
            "fte_nursing": "Nursing FTE",
            "nursing_fte_per_bed": "Nursing FTE per bed",
            "beds_per_nursing_fte": "Beds per nursing FTE",
        }
    )

    POWERBI.mkdir(exist_ok=True)
    merged.to_csv(POWERBI / "state_indicators_2023.csv", index=False)

    national = pd.read_csv(national_path).rename(
        columns={
            "year": "Year",
            "hospitals": "Hospitals",
            "beds": "Beds",
            "cases": "Inpatient cases",
            "avg_length_of_stay_days": "Avg length of stay (days)",
            "bed_occupancy_pct": "Bed occupancy %",
        }
    )
    national.to_csv(POWERBI / "national_trends.csv", index=False)

    print(f"Wrote {POWERBI / 'state_indicators_2023.csv'} ({len(merged)} states)")
    print(f"Wrote {POWERBI / 'national_trends.csv'} ({len(national)} years)")


if __name__ == "__main__":
    sys.exit(main())
