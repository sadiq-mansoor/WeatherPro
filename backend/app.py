"""
Weather Prediction API — NCAI, UET Peshawar
Flask backend serving LSTM-based weather forecasts for Peshawar.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import numpy as np
import joblib
import tensorflow as tf
import os
import sys
import hmac
import warnings
from datetime import datetime, timedelta, timezone
import logging
import threading
import time
import tempfile
from pathlib import Path

from weather_utils import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    dew_point_celsius,
    clamp,
    token_matches,
)

# -------------------------
# Environment & logging
# -------------------------
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = (
    str(Path(tempfile.gettempdir()) / "weather-pro")
    if os.getenv("VERCEL") == "1"
    else str(BASE_DIR)
)
DATA_DIR = Path(os.getenv("WEATHER_DATA_DIR", DEFAULT_DATA_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(DATA_DIR / "predictions.log"), logging.StreamHandler()],
)

app = Flask(__name__)
_cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
CORS(app, origins=_cors_origins or "*")

# -------------------------
# Constants
# -------------------------
MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "best_lstm.keras"))
SCALER_X_PATH = os.getenv("SCALER_X_PATH", str(BASE_DIR / "scaler_X.pkl"))
SCALER_Y_PATH = os.getenv("SCALER_Y_PATH", str(BASE_DIR / "scaler_y.pkl"))
WINDOW_FILE = os.getenv("WINDOW_FILE", str(DATA_DIR / "window.npy"))
HISTORY_FILE = os.getenv("HISTORY_FILE", str(DATA_DIR / "history.npy"))

API_KEY = os.getenv("OPENWEATHER_API_KEY")
# If ADMIN_TOKEN is unset every admin endpoint is disabled — no insecure default.
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

CITY = "peshawar"
BASE_URL = "https://api.openweathermap.org/data/2.5"

EXPECTED_WINDOW_SHAPE = (30, 5)  # 30-day rolling window, 5 features
FORECAST_STEPS = 7
WEATHER_CACHE_DURATION = 300     # seconds (5 minutes)

weather_cache: dict = {"data": None, "timestamp": 0.0}
cache_lock = threading.Lock()
window_lock = threading.Lock()   # guards window read/write and file saves

# -------------------------
# Load model & scalers
# -------------------------
def safe_load_model(path: str):
    try:
        m = tf.keras.models.load_model(path, compile=False)
        m.trainable = False

        @tf.function(experimental_relax_shapes=True)
        def optimized_predict(x):
            return m(x, training=False)

        m.optimized_predict = optimized_predict
        logging.info("Model loaded and optimized from %s", path)
        return m
    except Exception as e:
        logging.exception("Failed to load model at %s: %s", path, e)
        raise


def safe_load_scaler(path: str):
    try:
        s = joblib.load(path)
        logging.info("Scaler loaded from %s", path)
        return s
    except Exception as e:
        logging.exception("Failed to load scaler at %s: %s", path, e)
        raise


# Fail fast with a clear message if a required artifact is missing.
_required_artifacts = {
    MODEL_PATH: "trained LSTM model",
    SCALER_X_PATH: "input feature scaler",
    SCALER_Y_PATH: "output target scaler",
}
_missing = [
    f"{path} ({desc})"
    for path, desc in _required_artifacts.items()
    if not os.path.exists(path)
]
if _missing:
    logging.error("Missing required model artifact(s): %s", "; ".join(_missing))
    logging.error(
        "Place these files in the backend directory. See README.md → 'Model artifacts'."
    )
    sys.exit(1)

model = safe_load_model(MODEL_PATH)
scaler_X = safe_load_scaler(SCALER_X_PATH)
scaler_y = safe_load_scaler(SCALER_Y_PATH)

# -------------------------
# Initialize window / history
# -------------------------
def _load_npy_or_zeros(path: str, shape: tuple, ndim: int = 2) -> np.ndarray:
    if os.path.exists(path):
        try:
            arr = np.load(path)
            if arr.shape == shape:
                return arr
            logging.warning("%s shape %s != expected %s — resetting.", path, arr.shape, shape)
        except Exception:
            logging.exception("Failed to load %s — resetting.", path)
    arr = np.zeros(shape, dtype=np.float32)
    np.save(path, arr)
    return arr


window: np.ndarray = _load_npy_or_zeros(WINDOW_FILE, EXPECTED_WINDOW_SHAPE)
history: np.ndarray = _load_npy_or_zeros(
    HISTORY_FILE, (0, EXPECTED_WINDOW_SHAPE[1])
)

# -------------------------
# Weather fetching (thread-safe cache)
# -------------------------
def get_current_weather() -> dict | None:
    """Fetch current Peshawar weather from OpenWeatherMap; cached for 5 minutes."""
    global weather_cache
    current_time = time.time()

    with cache_lock:
        cached = weather_cache
        if (
            cached["data"] is not None
            and current_time - cached["timestamp"] < WEATHER_CACHE_DURATION
        ):
            response = cached["data"]
        else:
            if not API_KEY:
                logging.warning("OPENWEATHER_API_KEY is not set — skipping live fetch.")
                return None
            url = f"{BASE_URL}/weather"
            params = {"q": CITY, "appid": API_KEY, "units": "metric"}
            try:
                resp = requests.get(url, params=params, timeout=5)
                resp.raise_for_status()
                response = resp.json()
                weather_cache = {"data": response, "timestamp": current_time}
            except Exception as e:
                logging.warning("Weather API failed: %s", e)
                return None

    if not response:
        return None

    main = response.get("main", {})
    wind = response.get("wind", {})
    if "temp" not in main or "humidity" not in main:
        logging.error("Weather API response missing temp or humidity.")
        return None

    temp_c: float = float(main["temp"])
    humidity: float = float(main["humidity"])
    pressure: float = float(main.get("pressure", 1013))
    wind_speed: float = float(wind.get("speed", 0.0))

    # Magnus formula dew-point approximation (accurate to ±0.35 °C for RH 50–100 %)
    alpha = 17.625
    beta = 243.04  # °C
    gamma = (alpha * temp_c / (beta + temp_c)) + np.log(humidity / 100.0)
    dew_point_c: float = float(beta * gamma / (alpha - gamma))

    return {
        "pressure": pressure,
        "dew_point_f": dew_point_c * 9.0 / 5.0 + 32.0,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "temp_f": temp_c * 9.0 / 5.0 + 32.0,
        "temp_c": temp_c,
    }


# -------------------------
# Prediction helpers
# -------------------------
def _inverse_transform_batch(y_scaled_batch: np.ndarray) -> np.ndarray:
    """Inverse-transform a (N, K) scaled output; pads/trims to scaler width."""
    y = np.array(y_scaled_batch)
    if y.ndim != 2:
        y = y.reshape(-1, y.shape[-1])
    expected: int = getattr(scaler_y, "n_features_in_", y.shape[1])
    if y.shape[1] < expected:
        y = np.pad(y, ((0, 0), (0, expected - y.shape[1])), mode="constant")
    elif y.shape[1] > expected:
        y = y[:, :expected]
    try:
        return scaler_y.inverse_transform(y)
    except Exception:
        return y


def _parse_prediction(y_inv: np.ndarray) -> dict:
    """Convert inverse-transformed model output row to a JSON-ready dict."""
    y0 = y_inv.flatten()
    pred_temp_f   = float(y0[0]) if y0.size > 0 else 0.0
    pred_humidity = float(y0[1]) if y0.size > 1 else 0.0
    pred_wind     = float(y0[2]) if y0.size > 2 else 0.0
    # y0[3] is raw precip in mm (log1p-transformed at training, expm1 to recover).
    pred_rain_mm  = float(np.expm1(max(y0[3], 0.0))) if y0.size > 3 else 0.0

    pred_humidity = min(max(pred_humidity, 0.0), 100.0)
    pred_wind = max(pred_wind, 0.0)
    # Map precip mm → probability proxy: cap at 50 mm (heavy rain), scale to 100 %.
    pred_rain_pct = min(pred_rain_mm / 50.0 * 100.0, 100.0)
    pred_temp_c = (pred_temp_f - 32.0) * 5.0 / 9.0

    return {
        "temp_c": round(pred_temp_c, 2),
        "temp_f": round(pred_temp_f, 2),
        "wind_speed": round(pred_wind, 2),
        "humidity": round(pred_humidity, 2),
        "rain_probability": round(pred_rain_pct, 2),
    }


def predict_from_window_batch(windows_batch: np.ndarray) -> list:
    """Run the LSTM on a batch of (N, 30, 5) windows.

    Returns a list of (result_dict, raw_scaled_list, inv_transformed_list).
    """
    batch_size = windows_batch.shape[0]
    X_scaled = np.zeros_like(windows_batch)
    for i in range(batch_size):
        X_scaled[i] = scaler_X.transform(windows_batch[i])

    if hasattr(model, "optimized_predict"):
        y_scaled = model.optimized_predict(X_scaled).numpy()
    else:
        y_scaled = model.predict(X_scaled, verbose=0)

    y_inv = _inverse_transform_batch(y_scaled)
    results = []
    for i in range(batch_size):
        results.append((
            _parse_prediction(y_inv[i]),
            y_scaled[i].tolist(),
            y_inv[i].tolist(),
        ))
    return results


def predict_from_window(in_window: np.ndarray) -> tuple:
    """Convenience wrapper for a single 30×5 window."""
    return predict_from_window_batch(in_window.reshape(1, 30, 5))[0]


def _append_history_row(row: np.ndarray) -> None:
    """Append one feature row to history and flush to disk immediately."""
    global history
    row = np.array(row, dtype=np.float32).reshape(1, -1)
    with window_lock:
        history = np.vstack([history, row])
        np.save(HISTORY_FILE, history)


# -------------------------
# Admin auth helper
# -------------------------
def is_admin_authorized() -> bool:
    """Constant-time Bearer-token check.
    Returns False when ADMIN_TOKEN is unset (all admin routes disabled).
    """
    if not ADMIN_TOKEN:
        return False
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header[len("Bearer "):]
    return token_matches(token, ADMIN_TOKEN)


# -------------------------
# API Routes — public
# -------------------------
@app.route("/")
def home():
    return jsonify({
        "message": "Weather Prediction API — NCAI, UET Peshawar",
        "status": "running",
        "available_endpoints": [
            "GET  /health",
            "GET  /api/current",
            "GET  /api/forecast",
            "GET  /debug_predict (admin)",
            "POST /api/admin/verify",
            "GET  /api/admin/window",
            "POST /api/admin/update",
            "GET  /api/admin/history",
        ],
    }), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model_loaded": model is not None,
        "scalers_loaded": scaler_X is not None and scaler_y is not None,
    })


@app.route("/api/current", methods=["GET"])
def api_current():
    global window
    try:
        current_weather = get_current_weather()
        if current_weather:
            features = np.array(
                [
                    current_weather["pressure"],
                    current_weather["dew_point_f"],
                    current_weather["humidity"],
                    current_weather["wind_speed"],
                    current_weather["temp_f"],
                ],
                dtype=np.float32,
            )
            with window_lock:
                window = np.vstack([window[1:], features])
                np.save(WINDOW_FILE, window)
            _append_history_row(features)

        with window_lock:
            snap = window.copy()
        result, _, _ = predict_from_window(snap)
        return jsonify(result)
    except Exception as e:
        logging.exception("Error in /api/current")
        return jsonify({"error": str(e)}), 500


@app.route("/api/forecast", methods=["GET"])
def api_forecast():
    """7-day autoregressive forecast.

    Each step feeds the model's *predicted* feature values back as the next
    window row, so predictions genuinely diverge over time.
    """
    try:
        with window_lock:
            sim_window = window.copy()

        start_time = datetime.now(timezone.utc)
        results = []

        for step in range(FORECAST_STEPS):
            result, y_scaled, y_inv = predict_from_window(sim_window)
            step_time = start_time + timedelta(days=step + 1)
            result["timestamp"] = step_time.isoformat().replace("+00:00", "Z")
            results.append(result)

            if step < FORECAST_STEPS - 1:
                # Build the next input row from predicted values (converted back
                # to the input feature space: pressure, dew_point_f, humidity,
                # wind_speed, temp_f).  Pressure is not predicted — carry forward
                # the last known value.
                last_pressure = float(sim_window[-1, 0])
                pred_temp_f = result["temp_f"]
                pred_humidity = result["humidity"]
                pred_wind = result["wind_speed"]

                # Derive dew_point_f from predicted temp/humidity (Magnus)
                pred_temp_c = (pred_temp_f - 32.0) * 5.0 / 9.0
                alpha, beta = 17.625, 243.04
                h_ratio = max(pred_humidity, 1.0) / 100.0
                gamma = (alpha * pred_temp_c / (beta + pred_temp_c)) + np.log(h_ratio)
                pred_dew_c = float(beta * gamma / (alpha - gamma))
                pred_dew_f = pred_dew_c * 9.0 / 5.0 + 32.0

                next_row = np.array(
                    [last_pressure, pred_dew_f, pred_humidity, pred_wind, pred_temp_f],
                    dtype=np.float32,
                )
                sim_window = np.vstack([sim_window[1:], next_row])

        return jsonify({"forecast": results})
    except Exception as e:
        logging.exception("Error in /api/forecast")
        return jsonify({"error": str(e)}), 500


@app.route("/debug_predict", methods=["GET"])
def debug_predict():
    if not is_admin_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        with window_lock:
            snap = window.copy()
        result, raw_scaled, inv = predict_from_window(snap)
        return jsonify({
            "prediction": result,
            "raw_model_output": raw_scaled,
            "inverse_transformed": inv,
        })
    except Exception as e:
        logging.exception("debug_predict error")
        return jsonify({"error": str(e)}), 500


# -------------------------
# API Routes — admin
# -------------------------
@app.route("/api/admin/verify", methods=["POST"])
def admin_verify():
    if not is_admin_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"authorized": True})


@app.route("/api/admin/window", methods=["GET"])
def admin_get_window():
    if not is_admin_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        with window_lock:
            snap = window.tolist()
        return jsonify(snap)
    except Exception as e:
        logging.exception("Error in /api/admin/window")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/update", methods=["POST"])
def admin_update_window():
    """Replace the rolling prediction window.

    Body must be a JSON array with shape (30, 5).
    """
    if not is_admin_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        global window
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "No JSON body provided"}), 400

        new_window = np.array(data, dtype=np.float32)
        if new_window.shape != EXPECTED_WINDOW_SHAPE:
            return jsonify({
                "error": (
                    f"Invalid window shape {new_window.shape}. "
                    f"Expected {EXPECTED_WINDOW_SHAPE}."
                )
            }), 400
        if not np.isfinite(new_window).all():
            return jsonify({"error": "Window values must all be finite numbers."}), 400

        with window_lock:
            window = new_window
            np.save(WINDOW_FILE, window)
        return jsonify({"message": "Window updated successfully"})
    except Exception as e:
        logging.exception("Error in /api/admin/update")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/history", methods=["GET"])
def admin_get_history():
    """Return the accumulated sensor feature history (most recent 200 rows)."""
    if not is_admin_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        with window_lock:
            # Return last 200 rows to keep the response size reasonable
            recent = history[-200:].tolist() if len(history) > 0 else []
        return jsonify({
            "total_rows": int(len(history)),
            "rows_returned": len(recent),
            "features": ["pressure", "dew_point_f", "humidity", "wind_speed", "temp_f"],
            "history": recent,
        })
    except Exception as e:
        logging.exception("Error in /api/admin/history")
        return jsonify({"error": str(e)}), 500


# -------------------------
# Entry point
# -------------------------
if __name__ == "__main__":
    # Warm up the model so the first real request isn't slow.
    try:
        dummy = np.random.default_rng(0).random((1, 30, 5)).astype(np.float32)
        dummy_scaled = scaler_X.transform(dummy[0])
        _ = model.predict(np.expand_dims(dummy_scaled, 0), verbose=0)
        logging.info("Model pre-compiled successfully.")
    except Exception as e:
        logging.warning("Model pre-compilation failed: %s", e)

    logging.info("Starting Weather Prediction API on port 5000 …")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
