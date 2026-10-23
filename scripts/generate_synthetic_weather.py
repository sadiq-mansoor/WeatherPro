"""Generate a reproducible synthetic daily weather dataset for pipeline tests.

This data is intentionally synthetic. It is useful for checking ingestion,
training, evaluation, and deployment wiring when the licensed real dataset is
not available. It must never be presented as evidence of real-world forecast
skill.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate(start: str, end: str, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start, end=end, freq="D")
    n = len(dates)
    day_of_year = dates.dayofyear.to_numpy(dtype=float)
    years_since_start = (dates.year.to_numpy() - dates.year.min()).astype(float)
    seasonal = np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
    semiannual = np.sin(4 * np.pi * (day_of_year - 20) / 365.25)

    # Smooth autoregressive weather noise produces realistic persistence while
    # preserving a fully deterministic result for the same seed.
    ar = np.zeros(n, dtype=float)
    shocks = rng.normal(0, 1.8, n)
    for i in range(1, n):
        ar[i] = 0.82 * ar[i - 1] + shocks[i]

    temp_c = 25.0 + 12.0 * seasonal + 1.2 * semiannual + 0.025 * years_since_start + ar
    humidity = np.clip(58.0 - 16.0 * seasonal + rng.normal(0, 7.0, n), 12.0, 98.0)
    dew_point_c = temp_c - ((100.0 - humidity) / 5.0)
    pressure = 1012.0 - 5.0 * seasonal + rng.normal(0, 5.0, n)
    wind = np.clip(5.5 + 1.2 * semiannual + rng.normal(0, 2.2, n), 0.1, None)

    monsoon = np.clip(0.04 + 0.18 * np.maximum(seasonal, 0), 0.02, 0.24)
    rain_event = rng.random(n) < monsoon
    precip = np.where(rain_event, rng.gamma(shape=1.6, scale=5.5, size=n), 0.0)

    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "city": "Peshawar (synthetic)",
        "tavg": np.round(temp_c, 3),
        "dew_point": np.round(dew_point_c, 3),
        "humidity": np.round(humidity, 3),
        "wspd": np.round(wind, 3),
        "pressure": np.round(pressure, 3),
        "prcp": np.round(precip, 3),
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "synthetic" / "peshawar_weather_synthetic.csv",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame = generate(args.start, args.end, args.seed)
    frame.to_csv(args.output, index=False)
    print(f"wrote {len(frame)} synthetic daily rows to {args.output}")
    print(f"seed={args.seed}; source=synthetic; real-world accuracy claims are invalid")


if __name__ == "__main__":
    main()
