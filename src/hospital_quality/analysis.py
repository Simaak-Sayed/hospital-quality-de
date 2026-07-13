"""Run the analytical SQL queries and derive headline findings.

The SQL lives in ``sql/queries/*.sql`` so it is reviewable and runnable on its
own. This module executes those queries against the built SQLite database,
returns the results as pandas DataFrames, and computes a compact set of
plain-language findings (the numbers quoted in the README and dashboard).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

_QUERY_DIR = Path(__file__).resolve().parents[2] / "sql" / "queries"


def _run_sql_file(conn: sqlite3.Connection, name: str) -> pd.DataFrame:
    """Execute a named .sql file and return its result as a DataFrame."""
    sql = (_QUERY_DIR / name).read_text(encoding="utf-8")
    return pd.read_sql_query(sql, conn)


@dataclass
class AnalysisResult:
    """All analytical outputs in one place."""

    national_trends: pd.DataFrame
    capacity_by_state: pd.DataFrame
    staffing_by_state: pd.DataFrame
    findings: dict[str, object]


def run_analysis(db_path: str | Path) -> AnalysisResult:
    """Run every query and compute headline findings.

    Args:
        db_path: Path to the SQLite database built by the ETL step.

    Returns:
        An :class:`AnalysisResult` with the three result tables and a findings
        dict suitable for JSON export.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        national = _run_sql_file(conn, "national_trends.sql")
        capacity = _run_sql_file(conn, "capacity_by_state_2023.sql")
        staffing = _run_sql_file(conn, "staffing_by_state_2023.sql")
    finally:
        conn.close()

    findings = _derive_findings(national, capacity, staffing)
    return AnalysisResult(
        national_trends=national,
        capacity_by_state=capacity,
        staffing_by_state=staffing,
        findings=findings,
    )


def _pct_change(first: float, last: float) -> float:
    """Percentage change from first to last (rounded to 1 dp)."""
    if first == 0:
        return 0.0
    return round((last - first) / first * 100.0, 1)


def _derive_findings(
    national: pd.DataFrame,
    capacity: pd.DataFrame,
    staffing: pd.DataFrame,
) -> dict[str, object]:
    """Compute the plain-language headline numbers from the result tables."""
    first = national.iloc[0]
    last = national.iloc[-1]

    # Regional disparity: ratio of highest to lowest beds per 100k.
    cap = capacity.dropna(subset=["beds_per_100k"])
    top_beds = cap.iloc[0]
    bottom_beds = cap.iloc[-1]

    staff = staffing.dropna(subset=["beds_per_nursing_fte"])
    best_staff = staff.sort_values("beds_per_nursing_fte").iloc[0]
    worst_staff = staff.sort_values("beds_per_nursing_fte").iloc[-1]

    return {
        "period": {"first_year": int(first["year"]), "last_year": int(last["year"])},
        "hospitals": {
            "first": int(first["hospitals"]),
            "last": int(last["hospitals"]),
            "pct_change": _pct_change(first["hospitals"], last["hospitals"]),
        },
        "beds": {
            "first": int(first["beds"]),
            "last": int(last["beds"]),
            "pct_change": _pct_change(first["beds"], last["beds"]),
        },
        "cases": {
            "first": int(first["cases"]),
            "last": int(last["cases"]),
            "pct_change": _pct_change(first["cases"], last["cases"]),
        },
        "avg_length_of_stay_days": {
            "first": round(float(first["avg_length_of_stay_days"]), 1),
            "last": round(float(last["avg_length_of_stay_days"]), 1),
        },
        "bed_occupancy_pct": {
            "first": round(float(first["bed_occupancy_pct"]), 1),
            "last": round(float(last["bed_occupancy_pct"]), 1),
        },
        "beds_per_100k_2023": {
            "highest_state": top_beds["name_en"],
            "highest_value": float(top_beds["beds_per_100k"]),
            "lowest_state": bottom_beds["name_en"],
            "lowest_value": float(bottom_beds["beds_per_100k"]),
            "disparity_ratio": round(
                float(top_beds["beds_per_100k"]) / float(bottom_beds["beds_per_100k"]), 2
            ),
            "national_mean": round(float(cap["beds_per_100k"].mean()), 1),
        },
        "nursing_staffing_2023": {
            "leanest_state": worst_staff["name_en"],
            "leanest_beds_per_nurse_fte": float(worst_staff["beds_per_nursing_fte"]),
            "richest_state": best_staff["name_en"],
            "richest_beds_per_nurse_fte": float(best_staff["beds_per_nursing_fte"]),
        },
    }
