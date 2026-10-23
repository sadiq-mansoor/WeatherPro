"""Pure, dependency-light helpers for WeatherPro.

Kept separate from ``app.py`` so the core numeric and security logic can be
unit-tested without loading the TensorFlow model, scalers, or Flask app.
"""

import hmac


def celsius_to_fahrenheit(temp_c):
    """Convert a Celsius temperature to Fahrenheit."""
    return (temp_c * 9 / 5) + 32.0


def fahrenheit_to_celsius(temp_f):
    """Convert a Fahrenheit temperature to Celsius."""
    return (temp_f - 32.0) * 5.0 / 9.0


def dew_point_celsius(temp_c, humidity):
    """Approximate dew point (deg C) from temperature (deg C) and relative
    humidity (percent). Uses the simple ``T - (100 - RH)/5`` estimate."""
    return temp_c - ((100 - humidity) / 5.0)


def clamp(value, low, high):
    """Constrain ``value`` to the inclusive ``[low, high]`` range."""
    return max(low, min(value, high))


def token_matches(provided, expected):
    """Constant-time comparison of an admin token.

    Returns ``False`` when no ``expected`` token is configured, so admin
    access is disabled by default rather than accidentally open.
    """
    if not expected:
        return False
    return hmac.compare_digest(str(provided), str(expected))
