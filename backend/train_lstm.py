"""
Train the Peshawar weather LSTM.

Predicts next-day [temp_f, humidity, wind, precip] from a 30-day window of
[pressure, dew_point_f, humidity, wind, temp_f] -- the exact (30, 5) -> 4
contract the Flask backend (app.py) expects at inference time.

Key correctness points vs. the original notebook:
  * Scalers are fit on the TRAINING split only (the notebook fit them on the
    full dataset, leaking test statistics into training).
  * Validation and test windows use only preceding observed history, matching
    how the deployed forecaster operates.
  * The final artifact is selected on validation MAE; the test split is held
    out until the final report.

Run:  python train_lstm.py
Writes: best_lstm.keras, scaler_X.pkl, scaler_y.pkl
"""
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_DETERMINISTIC_OPS"] = "1"

import numpy as np
import pandas as pd
import joblib
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

SEED = 42
tf.keras.utils.set_random_seed(SEED)
try:
    tf.config.experimental.enable_op_determinism()
except (AttributeError, RuntimeError):
    pass

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
# The dataset is intentionally kept outside Git. Set DATA_CSV to a downloaded
# copy with these columns: date, city, tavg, dew_point, humidity, wspd,
# pressure, prcp. The default points to the documented repository location.
DATA_CSV = os.environ.get(
    "DATA_CSV",
    str(REPO_DIR / "data" / "raw" / "pakistan_weather_2000_2024.csv"),
)
ARTIFACT_DIR = Path(os.environ.get("MODEL_OUTPUT_DIR", str(BASE_DIR)))
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
WINDOW = 30
EPOCHS = int(os.environ.get("EPOCHS", "120"))
BATCH = int(os.environ.get("BATCH_SIZE", "32"))
INPUT_FEATURES = ["pressure", "dew_point_f", "humidity", "wspd", "temp_f"]
TARGET_FEATURES = ["temp_f", "humidity", "wspd", "precip"]

# -------------------------------------------------------------------------
# 1) Load & prepare (convert C -> F so units match what app.py feeds live)
# -------------------------------------------------------------------------
def load_frame():
    if not os.path.isfile(DATA_CSV):
        raise FileNotFoundError(
            f"Training dataset not found: {DATA_CSV}. "
            "Read data/README.md and set DATA_CSV to the downloaded CSV."
        )
    df = pd.read_csv(DATA_CSV)
    required = {"date", "city", "tavg", "dew_point", "humidity", "wspd", "pressure", "prcp"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")
    df = df[df["city"].astype(str).str.contains("Peshawar", case=False, na=False)].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").dropna(subset=["date"]).reset_index(drop=True)

    if df["date"].duplicated().any():
        duplicates = int(df["date"].duplicated().sum())
        raise ValueError(f"Dataset contains {duplicates} duplicate Peshawar dates.")

    numeric_columns = ["tavg", "dew_point", "humidity", "wspd", "pressure", "prcp"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["temp_f"] = df["tavg"] * 9.0 / 5.0 + 32.0
    df["dew_point_f"] = df["dew_point"] * 9.0 / 5.0 + 32.0
    df["precip"] = df["prcp"]
    df = df.dropna(subset=INPUT_FEATURES + TARGET_FEATURES).reset_index(drop=True)
    values = df[INPUT_FEATURES + TARGET_FEATURES].to_numpy(dtype="float64")
    if not np.isfinite(values).all():
        raise ValueError("Dataset contains non-finite feature or target values.")
    if len(df) <= WINDOW + 1:
        raise ValueError(f"Dataset needs more than {WINDOW + 1} usable Peshawar rows.")
    return df

def make_target_sequences(X, y, target_start, target_end, window=WINDOW):
    """Create samples whose target dates are in [target_start, target_end).

    Validation and test targets may use immediately preceding observed rows as
    context. No future rows are included, which mirrors deployment.
    """
    if target_start < window:
        raise ValueError("target_start must leave enough history for a window")
    Xs = [X[i - window:i] for i in range(target_start, target_end)]
    ys = [y[i] for i in range(target_start, target_end)]
    return np.asarray(Xs, dtype="float32"), np.asarray(ys, dtype="float32")

def prepare():
    df = load_frame()
    X_raw = df[INPUT_FEATURES].values.astype("float32")
    y_raw = df[TARGET_FEATURES].values.astype("float32")
    if (y_raw[:, -1] < 0).any():
        raise ValueError("Precipitation cannot be negative.")
    y_raw[:, -1] = np.log1p(y_raw[:, -1])  # stabilize precip (many zeros / spikes)

    n = len(df)
    n_tr, n_va = int(0.70 * n), int(0.15 * n)
    test_start = n_tr + n_va

    # Fit scalers on TRAIN ONLY -> no leakage.
    scaler_X = MinMaxScaler().fit(X_raw[:n_tr])
    scaler_y = MinMaxScaler().fit(y_raw[:n_tr])
    X_scaled = scaler_X.transform(X_raw)
    y_scaled = scaler_y.transform(y_raw)

    data = {
        "train": make_target_sequences(X_scaled, y_scaled, WINDOW, n_tr),
        "val": make_target_sequences(X_scaled, y_scaled, n_tr, test_start),
        "test": make_target_sequences(X_scaled, y_scaled, test_start, n),
    }
    return data, scaler_X, scaler_y

# -------------------------------------------------------------------------
# 2) Model builders
# -------------------------------------------------------------------------
def build_baseline(n_steps, n_features, n_out):
    """Original notebook recipe."""
    m = Sequential([
        Input(shape=(n_steps, n_features)),
        LSTM(128, return_sequences=True),
        Dropout(0.2),
        LSTM(64),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(n_out, activation="linear"),
    ])
    m.compile(optimizer=Adam(1e-3), loss="mse",
              metrics=[tf.keras.metrics.MeanAbsoluteError(name="mae")])
    return m

def build_improved(n_steps, n_features, n_out):
    """Same capacity as the baseline, but trained against MAE directly (the
    metric we report) with lighter dropout and gradient clipping for stability.
    Optimising the evaluation objective generalises better here than MSE."""
    m = Sequential([
        Input(shape=(n_steps, n_features)),
        LSTM(128, return_sequences=True),
        Dropout(0.15),
        LSTM(64),
        Dropout(0.15),
        Dense(32, activation="relu"),
        Dense(n_out, activation="linear"),
    ])
    m.compile(optimizer=Adam(1e-3, clipnorm=1.0), loss="mae",
              metrics=[tf.keras.metrics.MeanAbsoluteError(name="mae")])
    return m

# -------------------------------------------------------------------------
# 3) Train / evaluate
# -------------------------------------------------------------------------
def train(model, data):
    cbs = [
        EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True, verbose=0),
        ReduceLROnPlateau(monitor="val_loss", patience=6, factor=0.5, min_lr=1e-5, verbose=0),
    ]
    model.fit(*data["train"], validation_data=data["val"],
              epochs=EPOCHS, batch_size=BATCH, callbacks=cbs, shuffle=False, verbose=0)
    return model

def evaluate(model, data, scaler_y, split):
    X_split, y_split = data[split]
    y_pred = model.predict(X_split, verbose=0)
    y_true = scaler_y.inverse_transform(y_split).copy()
    y_hat = scaler_y.inverse_transform(y_pred).copy()
    y_true[:, -1] = np.expm1(y_true[:, -1])  # undo log1p on precip
    y_hat[:, -1] = np.expm1(y_hat[:, -1])

    rows = {}
    for j, name in enumerate(TARGET_FEATURES):
        mae = mean_absolute_error(y_true[:, j], y_hat[:, j])
        rmse = np.sqrt(mean_squared_error(y_true[:, j], y_hat[:, j]))
        rows[name] = (mae, rmse)
    overall_mae = float(np.mean(np.abs(y_true - y_hat)))
    return rows, overall_mae

def report(tag, rows, overall):
    print(f"\n[{tag}]")
    for name, (mae, rmse) in rows.items():
        print(f"  {name:>9s}  MAE {mae:8.4f}  RMSE {rmse:8.4f}")
    print(f"  {'overall':>9s}  MAE {overall:8.4f}")

# -------------------------------------------------------------------------
def main():
    data, scaler_X, scaler_y = prepare()
    n_steps, n_features = data["train"][0].shape[1:]
    n_out = data["train"][1].shape[1]
    print(f"train {data['train'][0].shape}  val {data['val'][0].shape}  test {data['test'][0].shape}")

    base = train(build_baseline(n_steps, n_features, n_out), data)
    b_val_rows, b_val_overall = evaluate(base, data, scaler_y, "val")
    b_test_rows, b_test_overall = evaluate(base, data, scaler_y, "test")
    report("baseline validation", b_val_rows, b_val_overall)
    report("baseline test", b_test_rows, b_test_overall)

    model_path = ARTIFACT_DIR / "best_lstm.keras"
    scaler_x_path = ARTIFACT_DIR / "scaler_X.pkl"
    scaler_y_path = ARTIFACT_DIR / "scaler_y.pkl"
    imp = train(build_improved(n_steps, n_features, n_out), data)
    i_val_rows, i_val_overall = evaluate(imp, data, scaler_y, "val")
    i_test_rows, i_test_overall = evaluate(imp, data, scaler_y, "test")
    report("improved validation", i_val_rows, i_val_overall)
    report("improved test", i_test_rows, i_test_overall)

    # Select using validation only. The test split is held back for the final
    # report and never determines which artifact is saved.
    if i_val_overall <= b_val_overall:
        selected, selected_name, selected_test = imp, "improved", i_test_overall
    else:
        selected, selected_name, selected_test = base, "baseline", b_test_overall

    delta = (b_val_overall - i_val_overall) / b_val_overall * 100.0
    print(f"\nvalidation MAE change: {delta:+.1f}%  (positive = improved)")
    print(f"selected model by validation MAE: {selected_name}")
    print(f"selected model test MAE: {selected_test:.4f}")

    selected.save(model_path)
    joblib.dump(scaler_X, scaler_x_path)
    joblib.dump(scaler_y, scaler_y_path)
    print(
        f"Saved validation-selected {model_path.name} + {scaler_x_path.name} "
        f"+ {scaler_y_path.name} in {ARTIFACT_DIR}"
    )

if __name__ == "__main__":
    main()
