-- Nursing and physician staffing intensity by federal state, 2023.
-- Personnel full-time equivalents (table 23111-12) are joined to bed capacity
-- (table 23111-09) to express staffing relative to the beds that must be
-- covered. nursing_fte_per_bed is the headline staffing-intensity indicator;
-- beds_per_nursing_fte is its more intuitive inverse (beds each nurse covers).
WITH staff AS (
    SELECT
        region,
        MAX(CASE WHEN measure = 'Vollkräfte im Jahresdurchschnitt insgesamt'
                 THEN value END)                                          AS fte_total,
        MAX(CASE WHEN measure = 'Vollkräfte im Jahresdurchschnitt ärztliches Personal'
                 THEN value END)                                          AS fte_physicians,
        MAX(CASE WHEN measure = 'Vollkräfte im Jahresdurchschnitt Nichtärztliches Personal davon Pflegedienst'
                 THEN value END)                                          AS fte_nursing
    FROM observations
    WHERE table_code = '23111-12'
      AND year = 2023
      AND dimension_1 = 'Krankenhäuser insgesamt'
    GROUP BY region
),
beds AS (
    SELECT
        region,
        MAX(CASE WHEN measure = 'Aufgestellte Betten insgesamt'
                 THEN value END)                                          AS beds
    FROM observations
    WHERE table_code = '23111-09'
      AND year = 2023
      AND dimension_1 = 'Krankenhäuser insgesamt'
    GROUP BY region
)
SELECT
    s.code,
    s.name_en,
    st.fte_total,
    st.fte_physicians,
    st.fte_nursing,
    b.beds,
    ROUND(st.fte_nursing / b.beds, 3)   AS nursing_fte_per_bed,
    ROUND(b.beds / st.fte_nursing, 2)   AS beds_per_nursing_fte
FROM states s
JOIN staff st ON s.region = st.region
JOIN beds  b  ON s.region = b.region
ORDER BY nursing_fte_per_bed DESC;
