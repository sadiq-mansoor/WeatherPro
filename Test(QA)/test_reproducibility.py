"""Reproducibility and sanity checks on model predictions.

The same input must always yield the same output (no hidden randomness at
inference), and predictions must stay inside physically meaningful bounds.
"""
import numpy as np
import pytest


@pytest.fixture
def fixed_window():
    # Deterministic pseudo-window in the model's input units:
    # pressure, dew_point_f, humidity, wind, temp_f
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
    assert first == second


def test_prediction_within_physical_ranges(module, fixed_window):
    result, _, _ = module.predict_from_window(fixed_window)
    assert 0.0 <= result["humidity"] <= 100.0
    assert result["wind_speed"] >= 0.0
    assert 0.0 <= result["rain_probability"] <= 100.0
    # Peshawar daily average temperature never leaves this envelope.
    assert -20.0 <= result["temp_c"] <= 60.0


def test_forecast_batch_matches_single(module, fixed_window):
    single, _, _ = module.predict_from_window(fixed_window)
    batch = module.predict_from_window_batch(fixed_window.reshape(1, 30, 5))
    assert batch[0][0] == single


def test_training_uses_fixed_seed():
    # Reproducible training runs rely on the seed being pinned in the script.
    import train_lstm
    assert train_lstm.SEED == 42
