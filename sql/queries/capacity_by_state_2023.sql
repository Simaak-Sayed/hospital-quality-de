-- Hospital bed capacity by federal state, 2023 (table 23111-09), joined to
-- population so capacity is comparable across states of very different size.
-- dimension_1 is pinned to the all-hospitals total to avoid double counting the
-- ownership/type breakdowns the source also stores in this table.
WITH capacity AS (
    SELECT
        s.code,
        s.name_en,
        s.region,
        s.population,
        MAX(CASE WHEN o.measure = 'Aufgestellte Betten insgesamt'
                 THEN o.value END)                                AS beds,
        MAX(CASE WHEN o.measure = 'Aufgestellte Betten darunter Intensivbetten'
                 THEN o.value END)                                AS icu_beds,
        MAX(CASE WHEN o.measure = 'Nutzungsgrad der Betten insgesamt'
                 THEN o.value END)                                AS utilization_pct
    FROM observations o
    JOIN states s ON o.region = s.region
    WHERE o.table_code = '23111-09'
      AND o.year = 2023
      AND o.dimension_1 = 'Krankenhäuser insgesamt'
    GROUP BY s.code, s.name_en, s.region, s.population
)
SELECT
    code,
    name_en,
    population,
    beds,
    icu_beds,
    utilization_pct,
    ROUND(beds * 100000.0 / population, 1)      AS beds_per_100k,
    ROUND(icu_beds * 100000.0 / population, 1)  AS icu_beds_per_100k
FROM capacity
ORDER BY beds_per_100k DESC;
