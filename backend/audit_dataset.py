"""Audit the approved weather CSV before training.

This command does not train a model or modify data. It reports the rows used,
date coverage, duplicates, gaps, missing values, and chronological split
boundaries so a training run has an auditable input contract.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_CSV = os.environ.get(
    "DATA_CSV",
    str(BASE_DIR.parent / "data" / "raw" / "pakistan_weather_2000_2024.csv"),
)
REQUIRED_COLUMNS = [
    "date", "city", "tavg", "dew_point", "humidity", "wspd", "pressure", "prcp"
]


def main():
    path = Path(DATA_CSV)
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Read data/README.md for the expected layout."
        )

    df = pd.read_csv(path)
    missing = sorted(set(REQUIRED_COLUMNS).difference(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df[df["city"].astype(str).str.contains("Peshawar", case=False, na=False)].copy()
    numeric = ["tavg", "dew_point", "humidity", "wspd", "pressure", "prcp"]
    for column in numeric:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    valid = df.dropna(subset=REQUIRED_COLUMNS).sort_values("date").reset_index(drop=True)
    dates = valid["date"]
    gaps = dates.diff().dropna().dt.days
    n = len(valid)
    train_end = int(0.70 * n)
    validation_end = train_end + int(0.15 * n)

    print(f"dataset: {path}")
    print(f"usable Peshawar rows: {n}")
    print(f"date range: {dates.min().date()} to {dates.max().date()}")
    print(f"duplicate dates: {int(dates.duplicated().sum())}")
    print(f"missing/invalid rows removed: {len(df) - n}")
    print(f"gaps greater than one day: {int((gaps > 1).sum())}")
    print(f"train target boundary: row 0 to {train_end - 1}")
    print(f"validation target boundary: row {train_end} to {validation_end - 1}")
    print(f"test target boundary: row {validation_end} to {n - 1}")

    values = valid[numeric].to_numpy(dtype="float64")
    if not np.isfinite(values).all():
        raise ValueError("The usable numeric data contains non-finite values.")
    if (valid["prcp"] < 0).any():
        raise ValueError("Precipitation contains negative values.")


if __name__ == "__main__":
    main()
