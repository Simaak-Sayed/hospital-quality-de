"""Render the charts used in the README from the analysis result tables.

Kept separate from the analysis so the numbers can be computed and tested
without a plotting backend. Uses a non-interactive matplotlib backend so it runs
headless in CI.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Polygon as MplPolygon

from hospital_quality.reference import STATE_CODE

INK = "#1f2933"
ACCENT = "#2a6db2"
ACCENT_2 = "#c0492f"
ACCENT_3 = "#3f8f4f"
GRID = "#dde3ea"

# Repository default location of the federal-state boundary file.
_DEFAULT_GEOJSON = Path(__file__).resolve().parents[2] / "data" / "geo" / "bundeslaender.geo.json"


def _style(ax: plt.Axes) -> None:
    """Apply a clean, consistent house style to an axis."""
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK)
    ax.title.set_color(INK)
    ax.yaxis.label.set_color(INK)
    ax.xaxis.label.set_color(INK)


def render_national_trends(national: pd.DataFrame, out_dir: Path) -> None:
    """Indexed trend lines (1991 = 100) plus the length-of-stay collapse."""
    df = national.dropna(subset=["hospitals", "beds", "cases"]).copy()
    base = df.iloc[0]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), dpi=140)

    for col, color, label in [
        ("hospitals", ACCENT, "Hospitals"),
        ("beds", ACCENT_2, "Beds"),
        ("cases", ACCENT_3, "Inpatient cases"),
    ]:
        ax1.plot(df["year"], df[col] / base[col] * 100.0, color=color, linewidth=2.2, label=label)
    ax1.axhline(100, color="#9aa5b1", linewidth=1, linestyle="--")
    _style(ax1)
    ax1.set_title("Capacity vs demand, indexed (1991 = 100)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Index (1991 = 100)")
    ax1.legend(frameon=False, fontsize=9)

    los = national.dropna(subset=["avg_length_of_stay_days"])
    ax2.plot(los["year"], los["avg_length_of_stay_days"], color=ACCENT, linewidth=2.4)
    ax2.fill_between(los["year"], los["avg_length_of_stay_days"], color=ACCENT, alpha=0.12)
    _style(ax2)
    ax2.set_title("Average length of stay (days)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Days")
    ax2.set_ylim(0, max(los["avg_length_of_stay_days"]) * 1.15)

    fig.tight_layout()
    fig.savefig(out_dir / "national_trends.png", bbox_inches="tight")
    plt.close(fig)


def render_beds_per_100k(capacity: pd.DataFrame, out_dir: Path) -> None:
    """Horizontal bar chart of beds per 100k inhabitants by state."""
    df = capacity.dropna(subset=["beds_per_100k"]).sort_values("beds_per_100k")
    mean = df["beds_per_100k"].mean()
    fig, ax = plt.subplots(figsize=(8, 6.4), dpi=140)
    ax.barh(df["name_en"], df["beds_per_100k"], color=ACCENT, zorder=3)
    ax.axvline(mean, color=ACCENT_2, linestyle="--", linewidth=1.4, zorder=4,
               label=f"National mean {mean:.0f}")
    _style(ax)
    ax.set_title("Hospital beds per 100,000 inhabitants by state (2023)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Beds per 100,000 inhabitants")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    for y, v in enumerate(df["beds_per_100k"]):
        ax.text(v + 4, y, f"{v:.0f}", va="center", fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(out_dir / "beds_per_100k_by_state.png", bbox_inches="tight")
    plt.close(fig)


def render_staffing(staffing: pd.DataFrame, out_dir: Path) -> None:
    """Horizontal bar chart of beds per nursing FTE by state (higher = leaner)."""
    df = staffing.dropna(subset=["beds_per_nursing_fte"]).sort_values("beds_per_nursing_fte")
    fig, ax = plt.subplots(figsize=(8, 6.4), dpi=140)
    colors = [ACCENT_2 if v >= df["beds_per_nursing_fte"].median() else ACCENT
              for v in df["beds_per_nursing_fte"]]
    ax.barh(df["name_en"], df["beds_per_nursing_fte"], color=colors, zorder=3)
    _style(ax)
    ax.set_title("Beds per nursing full-time equivalent by state (2023)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Beds per nursing FTE  (higher = leaner staffing)")
    for y, v in enumerate(df["beds_per_nursing_fte"]):
        ax.text(v + 0.01, y, f"{v:.2f}", va="center", fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(out_dir / "staffing_by_state.png", bbox_inches="tight")
    plt.close(fig)


def _exterior_rings(geometry: dict) -> list[list[list[float]]]:
    """Yield the exterior ring(s) of a GeoJSON Polygon or MultiPolygon."""
    kind = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if kind == "Polygon":
        return [coords[0]] if coords else []
    if kind == "MultiPolygon":
        return [poly[0] for poly in coords if poly]
    return []


def _largest_ring(rings: list[list[list[float]]]) -> list[list[float]]:
    """Return the ring with the most points (a cheap proxy for the main landmass)."""
    return max(rings, key=len) if rings else []


def render_choropleth(
    capacity: pd.DataFrame,
    out_dir: Path,
    value_col: str = "beds_per_100k",
    title: str = "Hospital beds per 100,000 inhabitants (2023)",
    cmap_name: str = "Blues",
    filename: str = "map_beds_per_100k.png",
    geojson_path: str | Path | None = None,
) -> None:
    """Render a choropleth map of the federal states shaded by ``value_col``.

    The federal-state boundaries come from a GeoJSON file; each feature is drawn
    as matplotlib polygons and filled from a sequential colour scale, so no
    heavyweight GIS dependency is needed. States are joined to the data through
    the German state name in the GeoJSON and the two-letter code in the data.

    Args:
        capacity: The per-state capacity table (must contain ``code`` and
            ``value_col``).
        out_dir: Directory to write the PNG into.
        value_col: Column to shade by.
        title: Chart title.
        cmap_name: Matplotlib colormap name.
        filename: Output file name.
        geojson_path: Boundary file; defaults to the repo's bundeslaender file.
    """
    geo = json.loads(Path(geojson_path or _DEFAULT_GEOJSON).read_text(encoding="utf-8"))
    value_by_code = dict(zip(capacity["code"], capacity[value_col], strict=False))
    values = [v for v in value_by_code.values() if pd.notna(v)]
    if not values:
        return
    norm = mcolors.Normalize(vmin=min(values), vmax=max(values))
    cmap = plt.get_cmap(cmap_name)

    fig, ax = plt.subplots(figsize=(6.6, 7.6), dpi=140)
    xs: list[float] = []
    ys: list[float] = []

    for feature in geo["features"]:
        german_name = feature["properties"].get("name")
        code = STATE_CODE.get(german_name)
        value = value_by_code.get(code)
        face = cmap(norm(value)) if value is not None and pd.notna(value) else "#e9edf1"

        rings = _exterior_rings(feature["geometry"])
        for ring in rings:
            ax.add_patch(MplPolygon(ring, closed=True, facecolor=face,
                                    edgecolor="white", linewidth=0.6, zorder=2))
            xs.extend(p[0] for p in ring)
            ys.extend(p[1] for p in ring)

        main = _largest_ring(rings)
        if main and code:
            cx = sum(p[0] for p in main) / len(main)
            cy = sum(p[1] for p in main) / len(main)
            ax.text(cx, cy, code, ha="center", va="center", fontsize=8,
                    fontweight="bold", color=INK, zorder=3)

    ax.set_xlim(min(xs) - 0.3, max(xs) + 0.3)
    ax.set_ylim(min(ys) - 0.3, max(ys) + 0.3)
    # Correct for latitude so Germany is not horizontally stretched.
    mid_lat = (min(ys) + max(ys)) / 2
    ax.set_aspect(1.0 / max(0.1, abs(math.cos(math.radians(mid_lat)))))
    ax.axis("off")
    ax.set_title(title, fontsize=12, fontweight="bold", color=INK)

    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02)
    cbar.ax.tick_params(labelsize=8, colors=INK)

    fig.tight_layout()
    fig.savefig(out_dir / filename, bbox_inches="tight")
    plt.close(fig)


def render_all(
    national: pd.DataFrame,
    capacity: pd.DataFrame,
    staffing: pd.DataFrame,
    out_dir: str | Path,
) -> None:
    """Render every README chart into ``out_dir``."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    render_national_trends(national, out)
    render_beds_per_100k(capacity, out)
    render_staffing(staffing, out)
    render_choropleth(capacity, out)
