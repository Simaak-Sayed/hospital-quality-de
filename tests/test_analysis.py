"""Integration test: build a small DB from synthetic records and run the analysis.

This exercises the real SQL query files and the findings derivation without
depending on the 2 MB source workbook, so it runs fast in CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hospital_quality.analysis import run_analysis
from hospital_quality.build_db import build_database
from hospital_quality.parse import Record


def _obs(table_code: str, region: str, measure: str, year: int, value: float,
         unit: str = "Anzahl", dim1: str | None = None) -> Record:
    return Record(
        table_code=table_code, statistic="Grunddaten der Krankenhäuser", region=region,
        dimension_1=dim1, dimension_2=None, measure=measure, year=year, unit=unit,
        value=value, value_flag=None,
    )


@pytest.fixture
def db(tmp_path: Path) -> str:
    """Build a minimal but query-compatible database."""
    total = "Krankenhäuser insgesamt"
    records: list[Record] = []

    # National time series (table 01), two years.
    for year, hosp, beds, cases, los, occ in [
        (1991, 2411, 665565, 14576612, 14.0, 84.1),
        (2023, 1874, 476924, 17202130, 7.2, 71.2),
    ]:
        records += [
            _obs("23111-01", "Deutschland", "Krankenhäuser insgesamt", year, hosp),
            _obs("23111-01", "Deutschland", "Krankenhäuser aufgestellte Betten insgesamt", year, beds),
            _obs("23111-01", "Deutschland", "Patientenbewegung Fallzahl", year, cases),
            _obs("23111-01", "Deutschland", "Patientenbewegung durchschnittliche Verweildauer", year, los, "in Tagen"),
            _obs("23111-01", "Deutschland", "Patientenbewegung durchschnittliche Bettenauslastung", year, occ, "in Prozent"),
        ]

    # Two states with capacity (table 09) and staffing (table 12), 2023.
    for region, beds, icu, util, nursing in [
        ("Bayern", 74000, 3800, 72.0, 60000),
        ("Bremen", 4131, 300, 70.0, 3877),
    ]:
        records += [
            _obs("23111-09", region, "Aufgestellte Betten insgesamt", 2023, beds, dim1=total),
            _obs("23111-09", region, "Aufgestellte Betten darunter Intensivbetten", 2023, icu, dim1=total),
            _obs("23111-09", region, "Nutzungsgrad der Betten insgesamt", 2023, util, "in Prozent", dim1=total),
            _obs("23111-12", region, "Vollkräfte im Jahresdurchschnitt insgesamt", 2023, nursing * 2, dim1=total),
            _obs("23111-12", region, "Vollkräfte im Jahresdurchschnitt ärztliches Personal", 2023, nursing // 3, dim1=total),
            _obs("23111-12", region, "Vollkräfte im Jahresdurchschnitt Nichtärztliches Personal davon Pflegedienst", 2023, nursing, dim1=total),
        ]

    db_path = tmp_path / "test.db"
    build_database(records, db_path)
    return str(db_path)


def test_national_trends_shape(db: str) -> None:
    result = run_analysis(db)
    assert list(result.national_trends["year"]) == [1991, 2023]
    assert result.national_trends.iloc[-1]["hospitals"] == 1874


def test_findings_capacity_and_disparity(db: str) -> None:
    findings = run_analysis(db).findings
    assert findings["hospitals"]["pct_change"] == pytest.approx(-22.3, abs=0.1)
    assert findings["beds"]["pct_change"] == pytest.approx(-28.3, abs=0.1)
    # Bremen has more beds per capita than Bavaria, so it should top the ranking.
    assert findings["beds_per_100k_2023"]["highest_state"] == "Bremen"
    assert findings["beds_per_100k_2023"]["disparity_ratio"] > 1.0


def test_staffing_join(db: str) -> None:
    staffing = run_analysis(db).staffing_by_state
    assert set(staffing["name_en"]) == {"Bavaria", "Bremen"}
    assert (staffing["nursing_fte_per_bed"] > 0).all()
