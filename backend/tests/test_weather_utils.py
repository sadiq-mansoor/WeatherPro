"""Unit tests for WeatherPro's pure helper functions.

These run without TensorFlow, the model files, or a network connection, so
they stay fast and green in CI.
"""

import os
import sys

import pytest

# make the backend package importable when tests run from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_utils import (  # noqa: E402
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    dew_point_celsius,
    clamp,
    token_matches,
)


@pytest.mark.parametrize("c, f", [(0, 32.0), (100, 212.0), (37, 98.6), (-40, -40.0)])
def test_celsius_to_fahrenheit(c, f):
    assert celsius_to_fahrenheit(c) == pytest.approx(f)


@pytest.mark.parametrize("f, c", [(32, 0.0), (212, 100.0), (-40, -40.0)])
def test_fahrenheit_to_celsius(f, c):
    assert fahrenheit_to_celsius(f) == pytest.approx(c)


def test_conversions_roundtrip():
    for c in (-15.0, 0.0, 21.5, 40.0):
        assert fahrenheit_to_celsius(celsius_to_fahrenheit(c)) == pytest.approx(c)


def test_dew_point_at_full_humidity_equals_temp():
    # at 100% relative humidity the dew point equals the air temperature
    assert dew_point_celsius(25.0, 100) == pytest.approx(25.0)


def test_dew_point_below_temperature_when_dry():
    # drier air -> dew point lower than the air temperature
    assert dew_point_celsius(30.0, 50) < 30.0
    assert dew_point_celsius(30.0, 50) == pytest.approx(30.0 - (50 / 5.0))


@pytest.mark.parametrize(
    "value, low, high, expected",
    [(150, 0, 100, 100), (-5, 0, 100, 0), (42, 0, 100, 42), (0.5, 0.0, 1.0, 0.5)],
)
def test_clamp(value, low, high, expected):
    assert clamp(value, low, high) == expected


def test_token_matches_correct():
    assert token_matches("s3cret-token", "s3cret-token") is True


def test_token_matches_wrong():
    assert token_matches("wrong", "s3cret-token") is False


def test_token_matches_disabled_when_unset():
    # if no admin token is configured, nothing should authorize
    assert token_matches("anything", None) is False
    assert token_matches("anything", "") is False
