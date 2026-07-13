-- National hospital trends, 1991-2023 (DESTATIS EVAS 23111, table 23111-01).
-- One row per year with the headline capacity and utilisation indicators.
-- Absolute counts carry unit 'Anzahl'; the year-over-year "Veraenderung" rows
-- are excluded by restricting to the value units we want.
SELECT
    o.year,
    MAX(CASE WHEN o.measure = 'Krankenhäuser insgesamt'
             THEN o.value END)                                    AS hospitals,
    MAX(CASE WHEN o.measure = 'Krankenhäuser aufgestellte Betten insgesamt'
             THEN o.value END)                                    AS beds,
    MAX(CASE WHEN o.measure = 'Patientenbewegung Fallzahl'
             THEN o.value END)                                    AS cases,
    MAX(CASE WHEN o.measure = 'Patientenbewegung durchschnittliche Verweildauer'
             THEN o.value END)                                    AS avg_length_of_stay_days,
    MAX(CASE WHEN o.measure = 'Patientenbewegung durchschnittliche Bettenauslastung'
             THEN o.value END)                                    AS bed_occupancy_pct
FROM observations o
WHERE o.table_code = '23111-01'
  AND o.region = 'Deutschland'
  AND o.unit IN ('Anzahl', 'in Tagen', 'in Prozent')
GROUP BY o.year
ORDER BY o.year;
