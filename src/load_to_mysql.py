# loads data/cleaned/cleaned_v1.csv into 4 MySQL tables

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
database = os.getenv("MYSQL_DATABASE")

engine = create_engine(
    f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

# load cleaned data
df = pd.read_csv("data/cleaned/cleaned_v1.csv", parse_dates=["date"])
print("Loaded cleaned_v1.csv:", df.shape)

# clearing existing rows
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
stations = (
    df[["station_name", "station_full_name", "station_zone"]]
    .drop_duplicates(subset="station_name")
    .rename(columns={"station_name": "station_code"})
)
stations.to_sql("stations", engine, if_exists="append", index=False)
print("Loaded stations:", len(stations))

# schedule table
schedule = (
    df[["train_no", "station_no", "station_name", "distance_from_origin"]]
    .drop_duplicates(subset=["train_no", "station_no"])
    .rename(columns={"station_name": "station_code"})
)
schedule.to_sql("schedule", engine, if_exists="append", index=False)
print("Loaded schedule:", len(schedule))

# delays table
delays = df[[
    "train_no", "station_name", "date", "station_no", "delay_minutes",
    "day_of_week", "month", "is_monsoon", "is_extreme_delay"
]].rename(columns={"station_name": "station_code", "date": "record_date"})

assert delays["delay_minutes"].isna().sum() == 0, "Unexpected nulls in delay_minutes"
delays.to_sql("delays", engine, if_exists="append", index=False, chunksize=5000)
print("Loaded delays:", len(delays))

# verify
with engine.connect() as conn:
    for table in ["trains", "stations", "schedule", "delays"]:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {count} rows in MySQL")

print("\nDone. delays row count in MySQL should match cleaned_v1.csv row count (262,256).")