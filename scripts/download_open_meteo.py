"""Download and validate Open-Meteo hourly archive data for Peshawar."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "raw" / "peshawar_weather_2000_2024.csv"
URL = "https://archive-api.open-meteo.com/v1/archive"
PARAMS = {
    "latitude": 34.008,
    "longitude": 71.5785,
    "start_date": "2000-01-01",
    "end_date": "2024-12-31",
    "hourly": "temperature_2m,relative_humidity_2m,dew_point_2m,wind_speed_10m,surface_pressure,precipitation",
    "timezone": "Asia/Karachi",
}
REQUIRED = ["date", "city", "tavg", "dew_point", "humidity", "wspd", "pressure", "prcp"]


def main() -> int:
    print("Fetching Open-Meteo hourly archive data for 2000-01-01 through 2024-12-31...")
    response = requests.get(URL, params=PARAMS, timeout=180)
    response.raise_for_status()
    payload = response.json()
    if "hourly" not in payload or "time" not in payload["hourly"]:
        raise ValueError("Open-Meteo response did not contain hourly time-series data")

    hourly = pd.DataFrame(payload["hourly"])
    hourly["time"] = pd.to_datetime(hourly["time"], errors="coerce")
    hourly = hourly.set_index("time").sort_index()
    if hourly.index.isna().any() or hourly.index.duplicated().any():
        raise ValueError("Hourly response contains invalid or duplicate timestamps")

    daily = hourly.resample("D").agg(
        {
            "temperature_2m": "mean",
            "dew_point_2m": "mean",
            "relative_humidity_2m": "mean",
            "wind_speed_10m": "mean",
            "surface_pressure": "mean",
            "precipitation": "sum",
        }
    ).round(2)
    daily = daily.rename(
        columns={
            "temperature_2m": "tavg",
            "dew_point_2m": "dew_point",
            "relative_humidity_2m": "humidity",
            "wind_speed_10m": "wspd",
            "surface_pressure": "pressure",
            "precipitation": "prcp",
        }
    ).reset_index(names="date")
    daily.insert(1, "city", "Peshawar")
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")

    if daily.columns.tolist() != REQUIRED:
        raise ValueError(f"Unexpected output columns: {daily.columns.tolist()}")
    numeric = daily[REQUIRED[2:]].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ValueError("Daily output contains missing or non-numeric weather values")
    if (daily["prcp"] < 0).any():
        raise ValueError("Daily precipitation contains negative values")
    if daily["date"].duplicated().any():
        raise ValueError("Daily output contains duplicate dates")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUTPUT, index=False)
    print(f"hourly rows: {len(hourly)}")
    print(f"daily rows: {len(daily)}")
    print(f"date range: {daily['date'].iloc[0]} to {daily['date'].iloc[-1]}")
    print(f"saved: {OUTPUT}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - clear command-line failure
        print(f"download failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
