import pandas as pd

EXCLUDED_STATIONS = ["KDV", "KARD", "NVRD", "KCVL", "BDMJ"]
EXTREME_DELAY_THRESHOLD = 1000

konkan_trains = pd.read_csv("data/reference/konkan_train_list.csv")["train_no"].tolist()

delay = pd.read_csv("data/raw/combined_delay.csv")
schedule = pd.read_csv("data/raw/combined_schedule.csv")
stations = pd.read_csv("data/raw/station_full_names.csv")
trains = pd.read_csv("data/raw/train_details.csv").drop_duplicates(subset="train_no", keep="first")

delay = delay[delay["train_no"].isin(konkan_trains)].copy()
print("Konkan delay rows:", len(delay))

print("\ndtypes:\n", delay.dtypes)
print("\nnulls per column:\n", delay.isna().sum())

dupe_count = delay.duplicated(subset=["date", "train_no", "station_no"]).sum()
print(f"\nDuplicate (date, train_no, station_no) rows: {dupe_count}")
delay = delay.drop_duplicates(subset=["date", "train_no", "station_no"])

unknown_stations = set(delay["station_name"]) - set(stations["station_name"])
unknown_trains = set(delay["train_no"]) - set(trains["train_no"])
print("Station codes with no match in station_full_names:", unknown_stations)
print("Train numbers with no match in train_details:", unknown_trains)

before = len(delay)
delay = delay[~delay["station_name"].isin(EXCLUDED_STATIONS)]
print(f"Dropped {before - len(delay)} rows from excluded stations")

delay["date"] = pd.to_datetime(delay["date"], errors="coerce")
bad_dates = delay["date"].isna().sum()
print(f"Rows with unparseable dates: {bad_dates}")
delay = delay.dropna(subset=["date"])

delay["day_of_week"] = delay["date"].dt.day_name()
delay["month"] = delay["date"].dt.month
delay["is_monsoon"] = delay["month"].isin([6, 7, 8, 9])

delay = delay.rename(columns={"delay": "delay_minutes"})
delay["delay_minutes"] = pd.to_numeric(delay["delay_minutes"], errors="coerce")

before = len(delay)
null_delay = delay["delay_minutes"].isna().sum()
delay_clean = delay.dropna(subset=["delay_minutes"]).copy()
print(f"Dropped {null_delay} rows with null delay_minutes ({null_delay / before * 100:.2f}%)")

delay_clean["is_extreme_delay"] = delay_clean["delay_minutes"] > EXTREME_DELAY_THRESHOLD

delay_clean = delay_clean.merge(
    stations[["station_name", "station_full_name", "station_zone"]],
    on="station_name", how="left"
)

delay_clean = delay_clean.merge(
    trains[["train_no", "train_name", "type_code"]],
    on="train_no", how="left"
)

sched_small = schedule[["train_no", "station_name", "distance_from_origin"]] \
    .drop_duplicates(subset=["train_no", "station_name"])
delay_clean = delay_clean.merge(
    sched_small, on=["train_no", "station_name"], how="left")

coverage = delay_clean.groupby("train_no")["date"].nunique()


def tier(days):
    if days >= 300:
        return "High"
    elif days >= 150:
        return "Medium"
    return "Low"


coverage_tier = coverage.apply(tier).rename("coverage_tier")
delay_clean = delay_clean.merge(coverage_tier, on="train_no", how="left")

print("\nFinal shape:", delay_clean.shape)
print(delay_clean.head())

delay_clean.to_csv("data/cleaned/cleaned_v1.csv", index=False)
print("Saved data/cleaned/cleaned_v1.csv")
