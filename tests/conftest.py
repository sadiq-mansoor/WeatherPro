import os
import sys

import pytest

# app.py loads the model and scalers by relative path when it is imported, and
# reads ADMIN_TOKEN from the environment at import time. Set the token and move
# into the backend directory before importing so those paths resolve.
BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("ADMIN_TOKEN", "test-token")
os.chdir(BACKEND)
sys.path.insert(0, BACKEND)

import app as weather_app  # noqa: E402


@pytest.fixture
def app():
    weather_app.app.config["TESTING"] = True
    return weather_app.app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def module():
    """Direct access to the app module for monkeypatching / model checks."""
    return weather_app


@pytest.fixture
def sample_weather():
    # Shape mirrors get_current_weather()'s return value.
    return {
        "pressure": 1008.0,
        "dew_point_f": 55.0,
        "humidity": 60.0,
        "wind_speed": 9.0,
        "temp_f": 78.0,
        "temp_c": 25.5,
    }
