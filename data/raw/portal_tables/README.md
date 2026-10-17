# Raw table captures from Älgdata

These CSV files are captured from tables rendered by the public Länsstyrelsen Älgdata statistics portal, rather than copied from a native Excel export. They preserve the source headings, grouped headers, summary rows, and explicit "no data" responses wherever the portal returned them.

- `hornean_*`: rows for Hörneåns ÄSO, 2020/2021–2025/2026 and current-boundary 2013/2014–2019/2020 captures.
- `hornean_algobs_ajo_historical_boundaries_2010-2020.csv`: additional Älgobs capture requested with historical boundaries; it returns seasons 2010/2011–2019/2020. Its first three seasons are available as a separately labelled normalized extension under `data/processed/`.
- `grasmyr_*`: report outputs for Gräsmyrs VVO, 2010/2011–2019/2020; some reports explicitly returned no data or zero sample counts.

The corresponding normalized rows for reports with data are under `data/processed/`. Never interpret a missing report row or "Tabellen innehåller ingen data" as zero harvest or zero observations without supporting evidence.