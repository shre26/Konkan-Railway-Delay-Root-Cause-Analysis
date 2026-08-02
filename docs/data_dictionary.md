# Data Dictionary — Konkan Railway Delay Root-Cause Analysis

Source: Kaggle — "Indian Railways Delay Dataset" (rxydenxd)
Date range: 2025-02-08 to 2026-02-07

## 1. combined_delay.csv (raw)
Per-station, per-day delay records for all Indian Railways trains.

| Column | Type | Description |
|---|---|---|
| date | string (YYYY-MM-DD) | Date of the recorded run |
| station_no | int | Sequence number of the station on that train's route (1 = origin) |
| station_name | string | Station code (join key to `station_full_names.csv`) |
| delay | float | Delay in minutes. Negative = early arrival. Null where not recorded. |
| train_no | int | Train number (join key to `train_details.csv`) |

Full size: 38,428,703 rows × 5 columns, 7,033 unique trains.
Konkan subset: 268,902 rows, 46 of 48 trains present.

## 2. combined_schedule.csv (raw)
Scheduled (not actual) timetable — station-by-station stops for every train.

| Column | Type | Description |
|---|---|---|
| station_no | int | Sequence number of the station on the route |
| station_name | string | Station code |
| distance_from_origin | int | Distance in km from the train's origin station |
| arrival_day | int | Day offset from departure day (1 = same day) |
| arrival_time | string (HH:MM) | Scheduled arrival time; blank at origin |
| departure_day | int | Day offset from departure day |
| departure_time | string (HH:MM) | Scheduled departure time; blank at terminus |
| train_no | int | Train number |

172,113 rows. Used as the reference for route order/distance, not for actual delay.

## 3. station_full_names.csv (raw)
Station code lookup.

| Column | Type | Description |
|---|---|---|
| station_name | string | Station code (join key) |
| station_full_name | string | Full station name |
| station_zone | string | Railway zone code (e.g. CR, WR) |
| station_address | string | Approximate location/address |

8,964 rows. Note: KCVL (one of the 5 excluded stations, see below) has no
matching entry in this file.

## 4. train_details.csv (raw)
Train number to name/type lookup.

| Column | Type | Description |
|---|---|---|
| train_no | int | Train number (join key) |
| train_name | string | Train name |
| type_code | string | Train category (e.g. EXP-TRAINS, SF-TRAINS, RAJ-TRAINS, T18-TRAINS, PRM-TRAINS) |

8,993 rows. **Known quirk**: a few trains (the Vande Bharats — 20645, 20646, 22229, 22230) have two rows each, under different `type_code` values. Deduplicated (keep first) when building the Konkan-only list.

## 5. konkan_train_list.csv (derived)
Filtered `train_details.csv` — the 48 Konkan Railway trains used to subset `combined_delay.csv`. Same columns as `train_details.csv` above. Built from a manually compiled list of Konkan-route train numbers, cross-checked against `combined_schedule.csv` to confirm real Konkan station sequences (e.g. BDTS→BVI→BSR→PNVL→ROHA→...→MAO).

## 6. cleaned/cleaned_v1.csv (derived)
Final cleaned and enriched dataset — one row per train, station, and date.
Built by `src/clean_data.py` from the four raw files above; this is the file
all EDA and analysis should read from.

| Column | Type | Description |
|---|---|---|
| date | datetime | Parsed from raw `date`, 0 unparseable rows |
| station_no | int | Sequence number of the station on the route |
| station_name | string | Station code |
| delay_minutes | float | Renamed from raw `delay`; null rows dropped |
| train_no | int | Train number |
| day_of_week | string | Derived from `date` (e.g. "Monday") |
| month | int | Derived from `date` (1–12) |
| is_monsoon | bool | True if `month` is Jun–Sep |
| is_extreme_delay | bool | True if `delay_minutes` > 1000 |
| station_full_name | string | From `station_full_names.csv` |
| station_zone | string | From `station_full_names.csv` |
| train_name | string | From `train_details.csv` |
| type_code | string | From `train_details.csv` |
| distance_from_origin | float | From `combined_schedule.csv`, km from train's origin |
| coverage_tier | string | High (≥300 days) / Medium (150–299) / Low (<150), per train |

262,256 rows × 15 columns (down from 268,902 raw Konkan rows — 1,147 dropped
for excluded stations, 5,499 dropped for null delay). Full reasoning for
every drop/keep decision is in `docs/decisions.md`.