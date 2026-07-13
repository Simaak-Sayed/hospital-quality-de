"""Reference data: German federal states, populations, and name normalisation.

The DESTATIS hospital tables report values by ``Gebiet`` (region), which is
either ``Deutschland`` (the national total) or one of the 16 federal states
(Bundeslaender). To compute per-capita indicators such as beds per 100,000
inhabitants, we join those regions to population figures held here.

Population source: Statistische Aemter des Bundes und der Laender
(statistikportal.de), reference date 31.12.2022. These are the last figures
before the 2022 census revision and are used consistently across all per-capita
metrics in this project.
"""

from __future__ import annotations

# Population by federal state, 31.12.2022 (persons).
# Keyed by the exact region label used in the DESTATIS workbook.
STATE_POPULATION_2022: dict[str, int] = {
    "Baden-Württemberg": 11_280_257,
    "Bayern": 13_369_393,
    "Berlin": 3_755_251,
    "Brandenburg": 2_573_135,
    "Bremen": 684_864,
    "Hamburg": 1_892_122,
    "Hessen": 6_391_360,
    "Mecklenburg-Vorpommern": 1_628_378,
    "Niedersachsen": 8_140_242,
    "Nordrhein-Westfalen": 18_139_116,
    "Rheinland-Pfalz": 4_159_150,
    "Saarland": 992_666,
    "Sachsen": 4_086_152,
    "Sachsen-Anhalt": 2_186_643,
    "Schleswig-Holstein": 2_953_270,
    "Thüringen": 2_126_846,
}

GERMANY_LABEL = "Deutschland"

# Short two-letter codes for compact dashboard labels and joins.
STATE_CODE: dict[str, str] = {
    "Baden-Württemberg": "BW",
    "Bayern": "BY",
    "Berlin": "BE",
    "Brandenburg": "BB",
    "Bremen": "HB",
    "Hamburg": "HH",
    "Hessen": "HE",
    "Mecklenburg-Vorpommern": "MV",
    "Niedersachsen": "NI",
    "Nordrhein-Westfalen": "NW",
    "Rheinland-Pfalz": "RP",
    "Saarland": "SL",
    "Sachsen": "SN",
    "Sachsen-Anhalt": "ST",
    "Schleswig-Holstein": "SH",
    "Thüringen": "TH",
}

# English-friendly ASCII names for readability in the English README/dashboard.
STATE_NAME_EN: dict[str, str] = {
    "Baden-Württemberg": "Baden-Wuerttemberg",
    "Bayern": "Bavaria",
    "Berlin": "Berlin",
    "Brandenburg": "Brandenburg",
    "Bremen": "Bremen",
    "Hamburg": "Hamburg",
    "Hessen": "Hesse",
    "Mecklenburg-Vorpommern": "Mecklenburg-Vorpommern",
    "Niedersachsen": "Lower Saxony",
    "Nordrhein-Westfalen": "North Rhine-Westphalia",
    "Rheinland-Pfalz": "Rhineland-Palatinate",
    "Saarland": "Saarland",
    "Sachsen": "Saxony",
    "Sachsen-Anhalt": "Saxony-Anhalt",
    "Schleswig-Holstein": "Schleswig-Holstein",
    "Thüringen": "Thuringia",
}


def is_state(region: str) -> bool:
    """Return True if the region label is one of the 16 federal states."""
    return region in STATE_POPULATION_2022


def population(region: str) -> int | None:
    """Return the population of a state, or None for non-state regions."""
    return STATE_POPULATION_2022.get(region)
