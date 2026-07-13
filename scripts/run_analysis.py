"""Run the analysis end to end: SQL -> tidy CSVs, findings JSON, and charts.

Outputs (all consumed by the README, the dashboard, and Power BI):
    data/processed/national_trends.csv
    data/processed/capacity_by_state_2023.csv
    data/processed/staffing_by_state_2023.csv
    results/findings.json
    assets/*.png

Usage:
    python scripts/run_analysis.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hospital_quality.analysis import run_analysis
from hospital_quality.charts import render_all

ROOT = Path(__file__).resolve().parents[1]


def main(db_path: str) -> None:
    """Run the analysis, write CSVs + findings JSON, and render charts."""
    if not Path(db_path).exists():
        raise SystemExit(f"Database not found: {db_path}. Run scripts/run_etl.py first.")

    result = run_analysis(db_path)

    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    result.national_trends.to_csv(processed / "national_trends.csv", index=False)
    result.capacity_by_state.to_csv(processed / "capacity_by_state_2023.csv", index=False)
    result.staffing_by_state.to_csv(processed / "staffing_by_state_2023.csv", index=False)

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "findings.json").write_text(
        json.dumps(result.findings, indent=2), encoding="utf-8"
    )

    render_all(result.national_trends, result.capacity_by_state, result.staffing_by_state,
               ROOT / "assets")

    f = result.findings
    print("Analysis complete.")
    print(f"  Hospitals {f['period']['first_year']}-{f['period']['last_year']}: "
          f"{f['hospitals']['first']:,} -> {f['hospitals']['last']:,} "
          f"({f['hospitals']['pct_change']}%)")
    print(f"  Beds: {f['beds']['first']:,} -> {f['beds']['last']:,} ({f['beds']['pct_change']}%)")
    print(f"  Cases: {f['cases']['first']:,} -> {f['cases']['last']:,} ({f['cases']['pct_change']}%)")
    print(f"  Avg length of stay: {f['avg_length_of_stay_days']['first']} -> "
          f"{f['avg_length_of_stay_days']['last']} days")
    print(f"  Beds per 100k spread: {f['beds_per_100k_2023']['lowest_state']} "
          f"{f['beds_per_100k_2023']['lowest_value']} .. "
          f"{f['beds_per_100k_2023']['highest_state']} "
          f"{f['beds_per_100k_2023']['highest_value']} "
          f"({f['beds_per_100k_2023']['disparity_ratio']}x)")
    print("  CSVs, findings.json, and charts written.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run hospital analysis and produce outputs")
    parser.add_argument("--db", default="data/processed/hospitals.db")
    args = parser.parse_args()
    main(args.db)
