# Raw data

This folder holds the source workbook from the German Federal Statistical
Office. It is committed here for reproducibility, but you can always re-download
the current edition yourself.

## File

`grunddaten_2023.xlsx` — *Statistischer Bericht: Grunddaten der Krankenhaeuser
2023*, Statistisches Bundesamt (Destatis), EVAS number 23111.

## How to (re)download

The workbook is published free of charge, with no login or order form, on the
Destatis publications page for hospital basic data:

> Destatis > Gesellschaft und Umwelt > Gesundheit > Krankenhaeuser >
> Publikationen > "Statistischer Bericht - Grunddaten der Krankenhaeuser"

Direct link (2023 edition):

    https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Gesundheit/Krankenhauser/Publikationen/Downloads-Krankenhaeuser/statistischer-bericht-grunddaten-krankenhaeuser-2120611237005.xlsx?__blob=publicationFile

Save the file here as `grunddaten_2023.xlsx`, then run `python scripts/run_etl.py`.

The workbook contains dozens of human-readable layout sheets plus a parallel set
of machine-readable `csv-23111-NN` sheets, which are what the parser reads.
