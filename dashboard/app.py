"""Interactive dashboard for the German hospital statistics analysis.

Reads the processed CSVs produced by ``scripts/run_analysis.py`` and presents
the national trends, regional capacity, and staffing findings. Run with:

    pip install -r requirements.txt
    python scripts/run_etl.py && python scripts/run_analysis.py
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
GEOJSON = ROOT / "data" / "geo" / "bundeslaender.geo.json"

sys.path.insert(0, str(ROOT / "src"))
from hospital_quality.reference import STATE_CODE  # noqa: E402

st.set_page_config(page_title="German Hospital Capacity", page_icon="🏥", layout="wide")


def _load_csv(name: str) -> pd.DataFrame:
    path = PROCESSED / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


national = _load_csv("national_trends.csv")
capacity = _load_csv("capacity_by_state_2023.csv")
staffing = _load_csv("staffing_by_state_2023.csv")
findings = (
    json.loads((RESULTS / "findings.json").read_text(encoding="utf-8"))
    if (RESULTS / "findings.json").exists()
    else {}
)

st.title("🏥 German Hospital Capacity & Staffing")
st.caption(
    "Analysis of the official federal hospital statistics (Statistisches Bundesamt, "
    "DESTATIS EVAS 23111). Built from scratch by Simaak Haque Fahimuddin Sayed. "
    "Research/portfolio use."
)

if national.empty:
    st.warning(
        "No processed data found. Run:\n\n"
        "```\npython scripts/run_etl.py\npython scripts/run_analysis.py\n```"
    )
    st.stop()


# --- Headline metrics -------------------------------------------------------

if findings:
    st.subheader("The story in five numbers (1991 to 2023)")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Hospitals", f"{findings['hospitals']['last']:,}",
              f"{findings['hospitals']['pct_change']}%")
    c2.metric("Beds", f"{findings['beds']['last']:,}",
              f"{findings['beds']['pct_change']}%")
    c3.metric("Inpatient cases", f"{findings['cases']['last']/1e6:.1f} M",
              f"{findings['cases']['pct_change']}%")
    c4.metric("Avg length of stay", f"{findings['avg_length_of_stay_days']['last']} d",
              f"{findings['avg_length_of_stay_days']['last'] - findings['avg_length_of_stay_days']['first']:.1f} d")
    c5.metric("Bed occupancy", f"{findings['bed_occupancy_pct']['last']}%",
              f"{findings['bed_occupancy_pct']['last'] - findings['bed_occupancy_pct']['first']:.1f} pp")
    st.caption(
        "Germany cut hospitals and beds sharply while treating more patients, made possible "
        "by average length of stay falling from 14 to about 7 days."
    )


# --- National trends --------------------------------------------------------

st.subheader("Capacity versus demand over time")
idx = national.dropna(subset=["hospitals", "beds", "cases"]).copy()
base = idx.iloc[0]
for col in ["hospitals", "beds", "cases"]:
    idx[col] = idx[col] / base[col] * 100.0
long = idx.melt("year", value_vars=["hospitals", "beds", "cases"],
                var_name="Series", value_name="Index (1991 = 100)")
chart = (
    alt.Chart(long)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("Index (1991 = 100):Q"),
        color=alt.Color("Series:N"),
        tooltip=["year", "Series", alt.Tooltip("Index (1991 = 100):Q", format=".1f")],
    )
    .properties(height=360)
)
st.altair_chart(chart, use_container_width=True)


# --- Regional map -----------------------------------------------------------

st.subheader("The regional picture (2023)")

_METRICS = {
    "Beds per 100,000 inhabitants": ("beds_per_100k", "Blues", capacity),
    "ICU beds per 100,000 inhabitants": ("icu_beds_per_100k", "Purples", capacity),
    "Beds per nursing FTE (leaner = higher)": ("beds_per_nursing_fte", "Reds", staffing),
}
choice = st.radio("Colour the map by:", list(_METRICS), horizontal=True)
value_col, scheme, source_df = _METRICS[choice]

if GEOJSON.exists() and not source_df.empty:
    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))
    value_by_code = dict(zip(source_df["code"], source_df[value_col], strict=False))
    name_by_code = dict(zip(capacity["code"], capacity["name_en"], strict=False))
    for feature in geo["features"]:
        code = STATE_CODE.get(feature["properties"].get("name"))
        feature["properties"]["metric"] = value_by_code.get(code)
        feature["properties"]["state"] = name_by_code.get(code, feature["properties"].get("name"))

    states = alt.Data(values=geo, format=alt.DataFormat(property="features", type="json"))
    map_chart = (
        alt.Chart(states)
        .mark_geoshape(stroke="white", strokeWidth=0.6)
        .encode(
            color=alt.Color("properties.metric:Q", title=choice,
                            scale=alt.Scale(scheme=scheme)),
            tooltip=[
                alt.Tooltip("properties.state:N", title="State"),
                alt.Tooltip("properties.metric:Q", title=choice, format=".1f"),
            ],
        )
        .project(type="mercator")
        .properties(height=520)
    )
    map_col, table_col = st.columns([3, 2])
    map_col.altair_chart(map_chart, use_container_width=True)
    ranked = source_df[["name_en", value_col]].dropna().sort_values(value_col, ascending=False)
    ranked.columns = ["State", choice]
    table_col.dataframe(ranked, hide_index=True, use_container_width=True, height=520)
else:
    st.info("Boundary file not found; skipping the map.")


# --- Regional capacity ------------------------------------------------------

left, right = st.columns(2)

with left:
    st.subheader("Beds per 100,000 by state (2023)")
    cap = capacity.dropna(subset=["beds_per_100k"]).sort_values("beds_per_100k")
    bar = (
        alt.Chart(cap)
        .mark_bar()
        .encode(
            x=alt.X("beds_per_100k:Q", title="Beds per 100,000 inhabitants"),
            y=alt.Y("name_en:N", sort="-x", title=None),
            tooltip=["name_en", "beds", "beds_per_100k"],
        )
        .properties(height=420)
    )
    st.altair_chart(bar, use_container_width=True)

with right:
    st.subheader("Beds per nursing FTE by state (2023)")
    st.caption("Higher means leaner staffing: each nurse covers more beds.")
    stf = staffing.dropna(subset=["beds_per_nursing_fte"]).sort_values("beds_per_nursing_fte")
    bar2 = (
        alt.Chart(stf)
        .mark_bar(color="#c0492f")
        .encode(
            x=alt.X("beds_per_nursing_fte:Q", title="Beds per nursing FTE"),
            y=alt.Y("name_en:N", sort="-x", title=None),
            tooltip=["name_en", "beds", "fte_nursing", "beds_per_nursing_fte"],
        )
        .properties(height=420)
    )
    st.altair_chart(bar2, use_container_width=True)


# --- Data tables ------------------------------------------------------------

with st.expander("View the underlying tables"):
    st.write("**Capacity by state (2023)**")
    st.dataframe(capacity, hide_index=True, use_container_width=True)
    st.write("**Staffing by state (2023)**")
    st.dataframe(staffing, hide_index=True, use_container_width=True)

st.divider()
st.caption(
    "Source: Statistisches Bundesamt (Destatis), Grunddaten der Krankenhäuser 2023 (EVAS 23111), "
    "own analysis. Population: Statistische Ämter des Bundes und der Länder, 31.12.2022."
)
