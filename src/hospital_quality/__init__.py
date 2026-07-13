"""Analysis of German federal hospital statistics (DESTATIS EVAS 23111).

A from-scratch data pipeline by Simaak Haque Fahimuddin Sayed: it downloads the
official 'Grunddaten der Krankenhaeuser' workbook, parses its machine-readable
sheets into tidy long data, loads them into SQLite, and computes capacity,
staffing, and regional-disparity indicators for Germany's ~1,900 hospitals.
"""

from __future__ import annotations

__version__ = "0.1.0"
