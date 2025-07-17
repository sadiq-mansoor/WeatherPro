from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import requests
import numpy as np
import joblib
import tensorflow as tf
import os
import sys
import hmac
import warnings
from datetime import datetime, timedelta
import logging
import threading
import time
from functools import lru_cache

# -------------------------
# Setup
# -------------------------
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("predictions.log"), logging.StreamHandler()]
)

app = Flask(__name__)
CORS(app)

# -------------------------
# Files & constants
# -------------------------
MODEL_PATH = "best_lstm.keras"
SCALER_X_PATH = "scaler_X.pkl"
SCALER_Y_PATH = "scaler_y.pkl"
WINDOW_FILE = "window.npy"
HISTORY_FILE = "history.npy"
API_KEY = os.getenv("OPENWEATHER_API_KEY")
# Read from env only. If unset, all admin endpoints are disabled (no insecure default).
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
CITY = "peshawar"
BASE_URL = "http://api.openweathermap.org/data/2.5"

EXPECTED_WINDOW_SHAPE = (30, 5)
FORECAST_STEPS = 7
WEATHER_CACHE_DURATION = 300  # 5 minutes cache
BATCH_PREDICTION_SIZE = 7

weather_cache = {"data": None, "timestamp": 0}
cache_lock = threading.Lock()

# -------------------------
# Load model & scalers
# -------------------------
def safe_load_model(path):
    try:
        m = tf.keras.models.load_model(path, compile=False)
        m.trainable = False

        @tf.function(experimental_relax_shapes=True)
        def optimized_predict(x):
            return m(x, training=False)
        m.optimized_predict = optimized_predict

        logging.info(f"Model loaded and optimized from {path}")
        return m
    except Exception as e:
        logging.exception(f"Failed to load model at {path}: {e}")
        raise

def safe_load_scaler(path):
    try:
        s = joblib.load(path)
        logging.info(f"Scaler loaded from {path}")
        return s
    except Exception as e:
        logging.exception(f"Failed to load scaler at {path}: {e}")
        raise

# Fail fast with a clear message if a required artifact is missing, instead of
# crashing mid-load with an opaque stack trace.
_required_artifacts = {
    MODEL_PATH: "trained LSTM model",
    SCALER_X_PATH: "input feature scaler",
    SCALER_Y_PATH: "output target scaler",
}
_missing = [f"{path} ({desc})" for path, desc in _required_artifacts.items() if not os.path.exists(path)]
if _missing:
    logging.error("Missing required model artifact(s): " + "; ".join(_missing))
    logging.error("Place these files in the backend directory. See README.md → 'Model artifacts'.")
    sys.exit(1)

model = safe_load_model(MODEL_PATH)
scaler_X = safe_load_scaler(SCALER_X_PATH)
scaler_y = safe_load_scaler(SCALER_Y_PATH)

# -------------------------
# Initialize window/history
# -------------------------
if os.path.exists(WINDOW_FILE):
    try:
        window = np.load(WINDOW_FILE)
        if window.shape != EXPECTED_WINDOW_SHAPE:
            logging.warning(f"{WINDOW_FILE} shape {window.shape} != expected {EXPECTED_WINDOW_SHAPE}, resetting.")
            window = np.zeros(EXPECTED_WINDOW_SHAPE, dtype=np.float32)
    except Exception:
        logging.exception("Failed to load window.npy, resetting.")
        window = np.zeros(EXPECTED_WINDOW_SHAPE, dtype=np.float32)
else:
    window = np.zeros(EXPECTED_WINDOW_SHAPE, dtype=np.float32)
    np.save(WINDOW_FILE, window)

if os.path.exists(HISTORY_FILE):
    try:
        history = np.load(HISTORY_FILE)
        if history.ndim != 2 or history.shape[1] != EXPECTED_WINDOW_SHAPE[1]:
            logging.warning("history.npy shape unexpected — resetting.")
            history = np.zeros((0, EXPECTED_WINDOW_SHAPE[1]), dtype=np.float32)
    except Exception:
        logging.exception("Failed to load history.npy — resetting.")
        history = np.zeros((0, EXPECTED_WINDOW_SHAPE[1]), dtype=np.float32)
else:
    history = np.zeros((0, EXPECTED_WINDOW_SHAPE[1]), dtype=np.float32)
    np.save(HISTORY_FILE, history)

# -------------------------
# Weather fetching (cached)
# -------------------------
@lru_cache(maxsize=1)
def get_cached_weather_data(cache_key):
    url = f"{BASE_URL}/weather"
    params = {"q": CITY, "appid": API_KEY, "units": "metric"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.exception(f"Weather API failed: {e}")
        return None

def get_current_weather():
    global weather_cache
    current_time = time.time()

    with cache_lock:
        if (weather_cache["data"] is not None and 
            current_time - weather_cache["timestamp"] < WEATHER_CACHE_DURATION):
            response = weather_cache["data"]
        else:
            cache_key = int(current_time // WEATHER_CACHE_DURATION)
            response = get_cached_weather_data(cache_key)
            if response:
                weather_cache["data"] = response
                weather_cache["timestamp"] = current_time

    if not response:
        return None

    main = response.get("main", {})
    wind = response.get("wind", {})
    if "temp" not in main or "humidity" not in main:
        logging.error("Weather API response missing temp or humidity.")
        return None

    temp_c = main.get("temp")
    humidity = main.get("humidity")
    pressure = main.get("pressure", 1013)
    dew_point_c = temp_c - ((100 - humidity) / 5.0)
    wind_speed = wind.get("speed", 0.0)

    return {
        "pressure": float(pressure),
        "dew_point_f": (dew_point_c * 9/5) + 32.0,
        "humidity": float(humidity),
        "wind_speed": float(wind_speed),
        "temp_f": (temp_c * 9/5) + 32.0,
        "temp_c": float(temp_c)
    }

# -------------------------
# Prediction functions
# -------------------------
def _ensure_y_shape_and_inverse_batch(y_scaled_batch):
    y_scaled_batch = np.array(y_scaled_batch)
    if y_scaled_batch.ndim != 2:
        y_scaled_batch = y_scaled_batch.reshape(-1, y_scaled_batch.shape[-1])
    expected = getattr(scaler_y, "n_features_in_", y_scaled_batch.shape[1])

    if y_scaled_batch.shape[1] < expected:
        pad = expected - y_scaled_batch.shape[1]
        y_scaled_batch = np.pad(y_scaled_batch, ((0, 0), (0, pad)), mode="constant")
    elif y_scaled_batch.shape[1] > expected:
        y_scaled_batch = y_scaled_batch[:, :expected]

    try:
        return scaler_y.inverse_transform(y_scaled_batch)
    except Exception:
        return y_scaled_batch

def predict_from_window_batch(windows_batch):
    batch_size = windows_batch.shape[0]
    X_scaled_batch = np.zeros_like(windows_batch)
    for i in range(batch_size):
        X_scaled_batch[i] = scaler_X.transform(windows_batch[i])

    if hasattr(model, 'optimized_predict'):
        y_pred_scaled_batch = model.optimized_predict(X_scaled_batch).numpy()
    else:
        y_pred_scaled_batch = model.predict(X_scaled_batch, verbose=0)

    y_pred_inv_batch = _ensure_y_shape_and_inverse_batch(y_pred_scaled_batch)
    results = []

    for i in range(batch_size):
        y0 = y_pred_inv_batch[i]
        if y0.size >= 4:
            pred_temp_f, pred_humidity, pred_wind, pred_rain = map(float, y0[:4])
        else:
            pred_temp_f = float(y0[0]) if y0.size > 0 else 0
            pred_humidity = float(y0[1]) if y0.size > 1 else 0
            pred_wind = float(y0[2]) if y0.size > 2 else 0
            pred_rain = float(y0[3]) if y0.size > 3 else 0

        pred_humidity = min(max(pred_humidity, 0.0), 100.0)
        pred_wind = max(pred_wind, 0.0)
        pred_rain_percentage = min(max(pred_rain, 0.0), 1.0) * 100.0
        if pred_rain_percentage > 100.0:
            pred_rain_percentage = 100.0
        pred_temp_c = (pred_temp_f - 32.0) * 5.0 / 9.0

        results.append((
            {
                "temp_c": round(pred_temp_c, 2),
                "temp_f": round(pred_temp_f, 2),
                "wind_speed": round(pred_wind, 2),
                "humidity": round(pred_humidity, 2),
                "rain_probability": round(pred_rain_percentage, 2)
            },
            y_pred_scaled_batch[i].tolist(),
            y_pred_inv_batch[i].tolist()
        ))
    return results

def predict_from_window(in_window):
    return predict_from_window_batch(in_window.reshape(1, 30, 5))[0]

def append_history_row(row):
    global history
    row = np.array(row, dtype=np.float32).reshape(1, -1)
    history = np.vstack([history, row])
    if history.shape[0] % 10 == 0:
        np.save(HISTORY_FILE, history)

# -------------------------
# API ROUTES
# -------------------------
@app.route("/")
def home():
    return jsonify({
        "message": "✅ Weather Prediction API is running successfully!",
        "available_endpoints": [
            "/api/current",
            "/api/forecast",
            "/api/admin/window",
            "/api/admin/update",
            "/api/admin/history",
            "/debug_predict",
            "/health"
        ]
    }), 200

@app.route("/api/current", methods=["GET"])
def api_current():
    global window
    try:
        current_weather = get_current_weather()
        if current_weather:
            features = np.array([
                current_weather["pressure"],
                current_weather["dew_point_f"],
                current_weather["humidity"],
                current_weather["wind_speed"],
                current_weather["temp_f"]
            ], dtype=np.float32)

            window = np.vstack([window[1:], features])
            threading.Thread(target=lambda: np.save(WINDOW_FILE, window), daemon=True).start()
            append_history_row(features)

        result, _, _ = predict_from_window(window)
        return jsonify(result)
    except Exception as e:
        logging.exception("Error in /api/current")
        return jsonify({"error": str(e)}), 500

@app.route("/api/forecast", methods=["GET"])
def api_forecast():
    try:
        sim_window = window.copy()
        windows_batch = []
        start_time = datetime.utcnow()

        for step in range(FORECAST_STEPS):
            windows_batch.append(sim_window.copy())
            if step < FORECAST_STEPS - 1:
                last_row = sim_window[-1].copy()
                sim_window = np.vstack([sim_window[1:], last_row])

        windows_batch = np.array(windows_batch)
        batch_results = predict_from_window_batch(windows_batch)

        results = []
        for step, (result, _, _) in enumerate(batch_results):
            step_time = start_time + timedelta(days=step + 1)
            result["timestamp"] = step_time.isoformat() + "Z"
            results.append(result)

        return jsonify({"forecast": results})
    except Exception as e:
        logging.exception("Error in /api/forecast")
        return jsonify({"error": str(e)}), 500

@app.route("/debug_predict", methods=["GET"])
def debug_predict():
    try:
        result, raw_scaled, inv = predict_from_window(window)
        return jsonify({
            "prediction": result,
            "raw_model_output": raw_scaled,
            "inverse_transformed": inv
        })
    except Exception as e:
        logging.exception("debug_predict error")
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_loaded": model is not None,
        "scalers_loaded": scaler_X is not None and scaler_y is not None
    })

# -------------------------
# RUN APP
# -------------------------

def is_admin_authorized():
    """Constant-time Bearer-token check. Returns False if ADMIN_TOKEN is unset
    (admin endpoints disabled) or the presented token does not match."""
    if not ADMIN_TOKEN:
        return False
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header[len("Bearer "):]
    return hmac.compare_digest(token, ADMIN_TOKEN)

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
        global window
        return jsonify(window.tolist())
    except Exception as e:
        logging.exception("Error in /api/admin/window")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/update", methods=["POST"])
def admin_update_window():
    if not is_admin_authorized():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        global window
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        window = np.array(data, dtype=np.float32)
        np.save(WINDOW_FILE, window)
        return jsonify({"message": "Window updated successfully"})
    except Exception as e:
        logging.exception("Error in /api/admin/update")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    try:
        dummy_input = np.random.random((1, 30, 5)).astype(np.float32)
        dummy_scaled = scaler_X.transform(dummy_input[0])
        dummy_scaled = np.expand_dims(dummy_scaled, axis=0)
        _ = model.predict(dummy_scaled, verbose=0)
        logging.info("Model pre-compiled for faster predictions.")
    except Exception as e:
        logging.warning(f"Model pre-compilation failed: {e}")

    logging.info("🚀 Starting optimized weather prediction server...")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
