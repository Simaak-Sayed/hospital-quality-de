# Power BI build guide

This project ships its cleaned, analysis-ready tables as CSVs in
`data/processed/`. This guide turns them into a Power BI report in about 15
minutes. The Streamlit app (`dashboard/app.py`) is the always-on, clickable
version of the same analysis; this Power BI build is the format most German
data-analyst job ads ask for.

> Why a guide and not a `.pbix` in the repo? A `.pbix` is an opaque binary that
> can only be produced by Power BI Desktop (Windows) and cannot be reviewed in a
> pull request. Shipping the clean CSVs plus these steps keeps the whole model
> transparent and reproducible, and it is exactly how a real BI handover works.

## 1. Load the data

In Power BI Desktop: **Home > Get data > Text/CSV**, and load all three files:

| File | Table name | Grain |
| --- | --- | --- |
| `data/processed/national_trends.csv` | `NationalTrends` | one row per year (1991-2023) |
| `data/processed/capacity_by_state_2023.csv` | `Capacity` | one row per federal state |
| `data/processed/staffing_by_state_2023.csv` | `Staffing` | one row per federal state |

Set data types: `year` to Whole Number; all rate/ratio columns to Decimal
Number. `Capacity` and `Staffing` share the `code`/`name_en` keys, so create a
relationship on `name_en` (or build a small `State` dimension from either).

## 2. Suggested DAX measures

```DAX
Beds per 100k (avg)   = AVERAGE ( Capacity[beds_per_100k] )
Total beds            = SUM ( Capacity[beds] )
Total ICU beds        = SUM ( Capacity[icu_beds] )
Nursing FTE per bed   = AVERAGE ( Staffing[nursing_fte_per_bed] )

Length of stay 2023   =
    CALCULATE ( MAX ( NationalTrends[avg_length_of_stay_days] ),
                NationalTrends[year] = 2023 )

Length of stay 1991   =
    CALCULATE ( MAX ( NationalTrends[avg_length_of_stay_days] ),
                NationalTrends[year] = 1991 )

Beds change since 1991 % =
VAR First = CALCULATE ( MAX ( NationalTrends[beds] ), NationalTrends[year] = 1991 )
VAR Last  = CALCULATE ( MAX ( NationalTrends[beds] ), NationalTrends[year] = 2023 )
RETURN DIVIDE ( Last - First, First )
```

## 3. Suggested visuals (one page)

1. **KPI cards** (top row): Hospitals 2023, Beds 2023, Inpatient cases 2023,
   Length of stay 2023, Bed occupancy 2023, each with the 1991 value or the
   change measure as the trend.
2. **Line chart**: `NationalTrends[year]` on the axis, with `hospitals`, `beds`,
   and `cases` as values. Index them to 1991 = 100 with a quick measure if you
   want the capacity-vs-demand framing from the README.
3. **Filled map** (Germany): location = `name_en`, colour saturation =
   `beds_per_100k`. Add a data-driven title.
4. **Clustered bar**: `Capacity[name_en]` sorted by `beds_per_100k`, with a
   constant line at the national average.
5. **Clustered bar**: `Staffing[name_en]` sorted by `beds_per_nursing_fte`.
6. **Slicer**: `name_en`, so a reviewer can focus on a single state.

## 4. Theme

Use a two-colour theme matching the Streamlit/README charts: primary
`#2A6DB2` (blue) for capacity, `#C0492F` (red) for staffing, on a white canvas.

Save as `powerbi/hospital-quality-de.pbix` and export a screenshot to
`assets/powerbi_report.png` for the README.
