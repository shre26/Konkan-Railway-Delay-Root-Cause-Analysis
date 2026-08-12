from datetime import datetime
from pathlib import Path

import meteostat as ms
import pandas as pd

START = datetime(2025, 2, 8)
END = datetime(2026, 2, 7)

REGIONS = {
    "Mumbai": (19.0760, 72.8777),
    "Ratnagiri": (16.9902, 73.3120),
    "Kankavli": (16.2667, 73.7000),
    "Sawantwadi": (15.9000, 73.8286),
    "Madgaon": (15.2832, 73.9862),
    "Mangalore": (12.9141, 74.8560),
}

# almost 47% data is missing for this station
EXCLUDED_FROM_CORRELATION = {"Kankavli"}

OUTPUT_PATH = Path("data/raw/weather/konkan_rainfall_meteostat.csv")

def find_nearest_stations(regions: dict) -> dict:
    station_map = {}
    for region, (lat, lon) in regions.items():
        point = ms.Point(lat, lon)
        nearby = ms.stations.nearby(point, limit=5)
        print(f"\n{region}: 5 nearest station candidates:")
        print(nearby[["name", "country", "distance"]])
        if not nearby.empty:
            station_map[region] = nearby.index[0]
    return station_map


def fetch_daily_weather(station_map: dict, start: datetime, end: datetime) -> pd.DataFrame:
    full_range = pd.date_range(start, end, freq="D")
    all_weather = []

    for region, station_id in station_map.items():
        data = ms.daily(station_id, start, end).fetch()
        data = data.reindex(full_range)
        data.index.name = "date"
        data = data.reset_index()
        data["region"] = region
        data["station_id"] = station_id
        all_weather.append(data)

    weather_df = pd.concat(all_weather, ignore_index=True)
    weather_df.rename(columns={"prcp": "rainfall_mm"}, inplace=True)
    return weather_df


def print_coverage_report(weather_df: pd.DataFrame) -> None:
    coverage = weather_df.groupby("region").agg(
        days_covered=("rainfall_mm", "count"),
        total_days=("date", "count"),
        pct_missing=("rainfall_mm", lambda x: x.isna().mean()),
    )
    print("\nCoverage by region:")
    print(coverage)

    print("\nMonsoon-window (Jun-Sep 2025) missing days by region:")
    for region in weather_df["region"].unique():
        sub = weather_df[weather_df["region"] == region]
        missing = sub[sub["rainfall_mm"].isna()]["date"]
        overlap = ((missing >= "2025-06-01") & (missing <= "2025-09-30")).sum()
        flag = " <- excluded from correlation" if region in EXCLUDED_FROM_CORRELATION else ""
        print(f"  {region}: {len(missing)} missing total, {overlap} inside monsoon{flag}")


def main():
    station_map = find_nearest_stations(REGIONS)
    print("\nSelected stations:")
    print(station_map)

    weather_df = fetch_daily_weather(station_map, START, END)
    print(f"\nFetched shape: {weather_df.shape}")

    print_coverage_report(weather_df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weather_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()