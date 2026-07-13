"""Load tidy hospital records into a queryable SQLite database.

The database has a deliberately simple, analysis-friendly shape:

* ``observations`` — one row per data cell from the DESTATIS csv sheets (the
  long fact table), with numeric values kept NULL when the source cell was a
  placeholder (see :mod:`hospital_quality.parse`).
* ``states`` — a small dimension table of the 16 federal states with population
  and codes, used for per-capita joins.

Keeping the fact table long (rather than pivoting to dozens of wide tables)
means new indicators are just new SQL queries, not schema changes.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from hospital_quality.parse import Record
from hospital_quality.reference import (
    STATE_CODE,
    STATE_NAME_EN,
    STATE_POPULATION_2022,
)

_SCHEMA = """
DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS states;

CREATE TABLE states (
    region      TEXT PRIMARY KEY,
    code        TEXT NOT NULL,
    name_en     TEXT NOT NULL,
    population  INTEGER NOT NULL
);

CREATE TABLE observations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    table_code  TEXT NOT NULL,
    statistic   TEXT,
    region      TEXT NOT NULL,
    dimension_1 TEXT,
    dimension_2 TEXT,
    measure     TEXT NOT NULL,
    year        INTEGER,
    unit        TEXT,
    value       REAL,
    value_flag  TEXT
);

CREATE INDEX idx_obs_table   ON observations (table_code);
CREATE INDEX idx_obs_region  ON observations (region);
CREATE INDEX idx_obs_measure ON observations (measure);
CREATE INDEX idx_obs_year    ON observations (year);
"""


def build_database(records: list[Record], db_path: str | Path) -> int:
    """Create a fresh SQLite database from parsed records.

    Args:
        records: Tidy records from :func:`hospital_quality.parse.parse_workbook`.
        db_path: Destination SQLite file (overwritten if it exists).

    Returns:
        The number of observation rows inserted.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_SCHEMA)

        conn.executemany(
            "INSERT INTO states (region, code, name_en, population) VALUES (?, ?, ?, ?)",
            [
                (region, STATE_CODE[region], STATE_NAME_EN[region], population)
                for region, population in STATE_POPULATION_2022.items()
            ],
        )

        conn.executemany(
            """
            INSERT INTO observations
                (table_code, statistic, region, dimension_1, dimension_2,
                 measure, year, unit, value, value_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    r.table_code,
                    r.statistic,
                    r.region,
                    r.dimension_1,
                    r.dimension_2,
                    r.measure,
                    r.year,
                    r.unit,
                    r.value,
                    r.value_flag,
                )
                for r in records
            ],
        )
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        return int(count)
    finally:
        conn.close()
