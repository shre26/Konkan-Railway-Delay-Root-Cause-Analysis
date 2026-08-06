import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
database = os.getenv("MYSQL_DATABASE")

engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

df = pd.read_csv("data/cleaned/cleaned_v1.csv", parse_dates=["date"])
print("Loaded cleaned_v1.csv:", df.shape)

raw_schedule = pd.read_csv("data/raw/combined_schedule.csv")

with engine.begin() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    conn.execute(text("TRUNCATE TABLE delays"))
    conn.execute(text("TRUNCATE TABLE schedule"))
    conn.execute(text("TRUNCATE TABLE stations"))
    conn.execute(text("TRUNCATE TABLE trains"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

print("Cleared existing rows")

# trains table
trains = (
    df[["train_no", "train_name", "type_code", "coverage_tier"]]
    .drop_duplicates(subset="train_no")
)

trains.to_sql("trains", engine, if_exists="append", index=False)

print("Loaded trains:", len(trains))

# stations table
konkan_train_nos = trains["train_no"].tolist()

schedule = (
    raw_schedule[raw_schedule["train_no"].isin(konkan_train_nos)]
    .drop_duplicates(subset=["train_no", "station_no"])
    .rename(columns={"station_name": "station_code"})
)

schedule = schedule[["train_no", "station_no", "station_code", "distance_from_origin", "arrival_day", "arrival_time", "departure_day", "departure_time"]]

stations_clean = (
    df[["station_name", "station_full_name", "station_zone"]]
    .rename(columns={"station_name": "station_code"})
)

stations_schedule = (
    schedule[["station_code"]]
    .drop_duplicates()
)

stations_schedule["station_full_name"] = None
stations_schedule["station_zone"] = None

stations = pd.concat(
    [stations_clean[["station_code", "station_full_name", "station_zone"]], stations_schedule[["station_code", "station_full_name", "station_zone"]]],
    ignore_index=True
)

stations["station_code"] = (
    stations["station_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

schedule["station_code"] = (
    schedule["station_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

stations = stations.drop_duplicates(subset="station_code")

stations.to_sql("stations", engine, if_exists="append",index=False)

print("Loaded stations:", len(stations))

# schedule table
missing_schedule_stations = (set(schedule["station_code"]) - set(stations["station_code"]))

if missing_schedule_stations:
    print("Missing schedule stations:", missing_schedule_stations)
    raise Exception("Schedule contains invalid station codes")

schedule.to_sql("schedule",engine,if_exists="append",index=False)

print("Loaded schedule:", len(schedule))

# delays table
delays = (
    df[["train_no", "station_name", "date", "station_no", "delay_minutes", "day_of_week", "month", "is_monsoon", "is_extreme_delay"]]
    .rename(columns={"station_name": "station_code", "date": "record_date"})
)

delays["station_code"] = (
    delays["station_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

missing_delay_stations = (
    set(delays["station_code"])
    - set(stations["station_code"])
)

if missing_delay_stations:
    print("Missing delay stations:", missing_delay_stations)
    raise Exception("Delays contains invalid station codes")

assert delays["delay_minutes"].isna().sum() == 0

delays.to_sql("delays", engine, if_exists="append", index=False, chunksize=5000)

print("Loaded delays:", len(delays))

with engine.connect() as conn:
    for table in ["trains", "stations", "schedule", "delays"]:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")
        ).scalar()
        print(f"{table}: {count} rows in MySQL")

print("\nDone. delays row count in MySQL should match cleaned_v1.csv row count (262,256).")