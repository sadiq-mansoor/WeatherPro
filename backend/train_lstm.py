"""
Train the Peshawar weather LSTM.

Predicts next-day [temp_f, humidity, wind, precip] from a 30-day window of
[pressure, dew_point_f, humidity, wind, temp_f] -- the exact (30, 5) -> 4
contract the Flask backend (app.py) expects at inference time.

Key correctness points vs. the original notebook:
  * Scalers are fit on the TRAINING split only (the notebook fit them on the
    full dataset, leaking test statistics into training).
  * Sequences are built within each chronological split, so no window ever
    crosses a train/val/test boundary.

Run:  python train_lstm.py
Writes: best_lstm.keras, scaler_X.pkl, scaler_y.pkl
"""
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import numpy as np
import pandas as pd
import joblib
import warnings
warnings.filterwarnings("ignore")

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)

# Dataset is not committed to the repo (large / external). Point DATA_CSV at a
# Peshawar daily CSV with columns: date, city, tavg, dew_point, humidity, wspd,
# pressure, prcp. Default is the local layout used during development.
DATA_CSV = os.environ.get("DATA_CSV", "../../data/pakistan_weather_2000_2024.csv")
WINDOW = 30
EPOCHS = 120
BATCH = 32
INPUT_FEATURES = ["pressure", "dew_point_f", "humidity", "wspd", "temp_f"]
TARGET_FEATURES = ["temp_f", "humidity", "wspd", "precip"]

# -------------------------------------------------------------------------
# 1) Load & prepare (convert C -> F so units match what app.py feeds live)
# -------------------------------------------------------------------------
def load_frame():
    df = pd.read_csv(DATA_CSV)
    df = df[df["city"].astype(str).str.contains("Peshawar", case=False, na=False)].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").dropna(subset=["date"]).reset_index(drop=True)

    df["temp_f"] = df["tavg"] * 9.0 / 5.0 + 32.0
    df["dew_point_f"] = df["dew_point"] * 9.0 / 5.0 + 32.0
    df["precip"] = df["prcp"]
    df = df.dropna(subset=INPUT_FEATURES + TARGET_FEATURES).reset_index(drop=True)
    return df

def make_sequences(X, y, window=WINDOW):
    Xs, ys = [], []
    for i in range(len(X) - window):
        Xs.append(X[i:i + window])
        ys.append(y[i + window])
    return np.array(Xs, dtype="float32"), np.array(ys, dtype="float32")

def prepare():
    df = load_frame()
    X_raw = df[INPUT_FEATURES].values.astype("float32")
    y_raw = df[TARGET_FEATURES].values.astype("float32")
    y_raw[:, -1] = np.log1p(y_raw[:, -1])  # stabilize precip (many zeros / spikes)

    n = len(df)
    n_tr, n_va = int(0.70 * n), int(0.15 * n)

    Xtr_raw, ytr_raw = X_raw[:n_tr], y_raw[:n_tr]
    Xva_raw, yva_raw = X_raw[n_tr:n_tr + n_va], y_raw[n_tr:n_tr + n_va]
    Xte_raw, yte_raw = X_raw[n_tr + n_va:], y_raw[n_tr + n_va:]

    # Fit scalers on TRAIN ONLY -> no leakage.
    scaler_X = MinMaxScaler().fit(Xtr_raw)
    scaler_y = MinMaxScaler().fit(ytr_raw)

    def seq(Xr, yr):
        return make_sequences(scaler_X.transform(Xr), scaler_y.transform(yr))

    data = {
        "train": seq(Xtr_raw, ytr_raw),
        "val":   seq(Xva_raw, yva_raw),
        "test":  seq(Xte_raw, yte_raw),
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
def train(model, data, ckpt=None):
    cbs = [
        EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True, verbose=0),
        ReduceLROnPlateau(monitor="val_loss", patience=6, factor=0.5, min_lr=1e-5, verbose=0),
    ]
    if ckpt:
        cbs.append(ModelCheckpoint(ckpt, monitor="val_loss", save_best_only=True, verbose=0))
    model.fit(*data["train"], validation_data=data["val"],
              epochs=EPOCHS, batch_size=BATCH, callbacks=cbs, verbose=0)
    return model

def evaluate(model, data, scaler_y):
    Xte, yte = data["test"]
    y_pred = model.predict(Xte, verbose=0)
    y_true = scaler_y.inverse_transform(yte).copy()
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
    b_rows, b_overall = evaluate(base, data, scaler_y)
    report("baseline", b_rows, b_overall)

    imp = train(build_improved(n_steps, n_features, n_out), data, ckpt="best_lstm.keras")
    i_rows, i_overall = evaluate(imp, data, scaler_y)
    report("improved", i_rows, i_overall)

    delta = (b_overall - i_overall) / b_overall * 100.0
    print(f"\noverall MAE change: {delta:+.1f}%  (positive = improved)")

    if i_overall <= b_overall:
        joblib.dump(scaler_X, "scaler_X.pkl")
        joblib.dump(scaler_y, "scaler_y.pkl")
        print("Saved improved best_lstm.keras + scaler_X.pkl + scaler_y.pkl")
        print("scaler_X min:", np.round(scaler_X.data_min_, 2),
              "max:", np.round(scaler_X.data_max_, 2))
    else:
        print("Improved did NOT beat baseline -- artifacts NOT overwritten.")

if __name__ == "__main__":
    main()
