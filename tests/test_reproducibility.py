"""Reproducibility and sanity checks on model predictions.

The same input must always yield the same output (no hidden randomness at
inference), and predictions must stay inside physically meaningful bounds.
"""
import numpy as np
import pytest


@pytest.fixture
def fixed_window():
    # Deterministic pseudo-window in the model's input units:
    # pressure, dew_point_f, humidity, wind_speed, temp_f
    rng = np.random.default_rng(1234)
    win = np.column_stack([
        rng.uniform(995, 1020, 30),
        rng.uniform(40, 70, 30),
        rng.uniform(30, 90, 30),
        rng.uniform(3, 20, 30),
        rng.uniform(60, 95, 30),
    ]).astype(np.float32)
    return win


def test_prediction_is_deterministic(module, fixed_window):
    first, _, _ = module.predict_from_window(fixed_window)
    second, _, _ = module.predict_from_window(fixed_window)
    assert first == second, "Prediction is not deterministic for the same input"


def test_prediction_within_physical_ranges(module, fixed_window):
    result, _, _ = module.predict_from_window(fixed_window)
    assert 0.0 <= result["humidity"] <= 100.0, f"Humidity out of range: {result['humidity']}"
    assert result["wind_speed"] >= 0.0, f"Negative wind speed: {result['wind_speed']}"
    assert 0.0 <= result["rain_probability"] <= 100.0, (
        f"Rain probability out of range: {result['rain_probability']}"
    )
    # Peshawar daily temperature envelope (conservative bounds)
    assert -20.0 <= result["temp_c"] <= 60.0, f"Temperature out of range: {result['temp_c']}"


def test_forecast_batch_matches_single(module, fixed_window):
    single, _, _ = module.predict_from_window(fixed_window)
    batch = module.predict_from_window_batch(fixed_window.reshape(1, 30, 5))
    assert batch[0][0] == single, "Batch prediction differs from single prediction"


def test_training_seed_is_pinned():
    """The training script must pin SEED = 42 for reproducible model builds.

    This test imports only the SEED constant — it does *not* trigger model
    loading or any file-system access — so it runs safely in any environment.
    """
    import importlib.util
    import os
    import sys

    backend_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "backend")
    )
    spec_path = os.path.join(backend_dir, "train_lstm.py")
    if not os.path.exists(spec_path):
        pytest.skip("train_lstm.py not found — skipping seed check")

    # Parse SEED without executing the full training script.
    seed_value = None
    with open(spec_path) as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith("SEED") and "=" in stripped:
                try:
                    seed_value = int(stripped.split("=")[1].strip())
                except ValueError:
                    pass
                break

    assert seed_value is not None, "SEED constant not found in train_lstm.py"
    assert seed_value == 42, f"Expected SEED=42, got {seed_value}"
