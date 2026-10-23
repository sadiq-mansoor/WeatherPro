"""Collect current and forecast weather from OpenWeather.

The API key is read from OPENWEATHER_API_KEY and is never written to disk.
Current observations are appended to data/live/openweather_observations.csv.
Forecast responses are saved as timestamped JSON snapshots for later
verification; forecasts must not be treated as observed training labels.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "live"
CURRENT_CSV = OUTPUT_DIR / "openweather_observations.csv"
LATITUDE = float(os.environ.get("OPENWEATHER_LAT", "34.0151"))
LONGITUDE = float(os.environ.get("OPENWEATHER_LON", "71.5249"))
CITY = os.environ.get("OPENWEATHER_CITY", "Peshawar")
BASE_URL = "https://api.openweathermap.org/data/2.5"
FIELDS = ["observed_at_utc", "date", "city", "lat", "lon", "tavg", "dew_point", "humidity", "wspd", "pressure", "prcp"]


def fetch(path: str, api_key: str) -> dict:
    query = urlencode({"lat": LATITUDE, "lon": LONGITUDE, "appid": api_key, "units": "metric"})
    request = Request(f"{BASE_URL}/{path}?{query}", headers={"User-Agent": "WeatherForecastingProfessional/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> int:
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        print("OPENWEATHER_API_KEY is required; no request was made.", file=sys.stderr)
        return 2

    try:
        current = fetch("weather", api_key)
        forecast = fetch("forecast", api_key)
    except Exception as exc:  # noqa: BLE001 - preserve provider error for operator
        print(f"OpenWeather request failed: {exc}", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    main_data = current.get("main", {})
    wind = current.get("wind", {})
    rain = current.get("rain", {})
    row = {
        "observed_at_utc": now.isoformat(),
        "date": now.date().isoformat(),
        "city": CITY,
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "tavg": main_data.get("temp"),
        "dew_point": None,
        "humidity": main_data.get("humidity"),
        "wspd": (wind.get("speed") or 0) * 3.6,
        "pressure": main_data.get("pressure"),
        "prcp": rain.get("1h", 0.0),
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not CURRENT_CSV.exists()
    with CURRENT_CSV.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    (OUTPUT_DIR / f"forecast_{stamp}.json").write_text(
        json.dumps({"retrieved_at_utc": now.isoformat(), "response": forecast}, indent=2),
        encoding="utf-8",
    )
    print(f"saved current observation to {CURRENT_CSV}")
    print(f"saved forecast snapshot to {OUTPUT_DIR / f'forecast_{stamp}.json'}")
    print("Note: current observations are suitable for future evaluation after enough collection; forecast values are not training labels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
