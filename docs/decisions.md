# Project Decisions Log

Konkan Railway Delay Root-Cause Analysis — key scoping and data decisions,
recorded as they were made so the reasoning survives past the moment.

## Scope 
- **Corridor**: Mumbai (CSMT/Panvel) to Madgaon, covering major Konkan Railway
  stations (Panvel, Roha, Khed, Chiplun, Ratnagiri, Kankavli, Sawantwadi,
  Thivim, Madgaon).
- **Trains**: 48 trains manually identified as running the Konkan corridor,
  cross-checked against actual route data (see `data/reference/konkan_train_list.csv`).
- **Metric**: arrival delay in minutes (`delay_minutes`), not departure delay.
- **Time window**: 1 year — matches the dataset's actual coverage
  (2025-02-08 to 2026-02-07).
- **Dataset**: Kaggle "Indian Railways Delay Dataset" (rxydenxd) — chosen
  after confirming no official source (data.gov.in, NTES) offers bulk
  historical delay data; data.gov.in only has scheduled timetables.

## Station Exclusions
Five stations — KDV, KARD, NVRD, KCVL, BDMJ — were excluded from analysis.
They show 93–99% missing delay values, indicating the data was never
collected at these stops rather than lost at random. KCVL also has no entry
in the station reference table, confirming this is broken data rather than
a partial gap. Missingness elsewhere is not date-driven (max ~5% missing on
any single day), so no seasonal bias is introduced by this exclusion.

## Missing Value Handling
Remaining null delay values (2.05% of rows after station exclusion, 5,499
records) were dropped, not imputed. Fabricating a delay value would inject
false signal into a root-cause analysis whose entire purpose is to detect
real disruption patterns.

## Duplicate Records
No duplicates found on the (date, train_no, station_no) key — one delay
observation per train per stop per day, as expected. No action needed.

## Extreme Delay Treatment
Delays over 1000 minutes (8 records) were kept and flagged via
`is_extreme_delay`, not removed as outliers. Checking them individually
showed a consistent pattern — the same train, same date, across consecutive
stations with delay building coherently (e.g. train 11004 on 2025-06-10;
multiple trains disrupted together on 2025-08-19). This is the signature of
genuine disruption events, likely monsoon-related, which is exactly what
this project aims to explain — not data errors to be cleaned away.

## Negative Delay Values
Negative values (early arrivals) are concentrated at terminus and major
junction stations (MAO, MAQ, LTT, NZM, CSMT, TVC, etc.) — consistent with
scheduled recovery/slack time built into timetables at these points. Kept
as-is; not a data error.

## Coverage Tiers
Trains are tiered by number of days with data: High (≥300 days), Medium
(150–299), Low (<150). Only High-tier trains should be used for full-year
seasonal or trend claims; a quarter of trains fall below 104 days and
cannot support that kind of analysis reliably.

## Cleaned Dataset
`data/cleaned/cleaned_v1.csv` (262,256 rows) is the delay data after all
exclusions above, merged with station names/zone, train name/type, and
route distance from `combined_schedule.csv`. Built by `src/clean_data.py`,
which is the source of truth — rerun it rather than hand-editing the CSV.