"""
Put the LSTM's test-set error in context against the two baselines every
weather-forecasting evaluation should report:

  * Persistence  -- "tomorrow = today". A deceptively strong baseline for
    daily data; a model that cannot beat it is not adding value.
  * Climatology  -- the training-set average for that calendar month.

It also scores precipitation as a rain / no-rain event (POD, FAR, CSI), which
is the honest way to judge rain in a dry climate -- plain MAE flatters any
model that just predicts "no rain".

Run from backend/ after training:  python evaluate_baselines.py
"""
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import numpy as np
import warnings
warnings.filterwarnings("ignore")

import tensorflow as tf
from sklearn.metrics import mean_absolute_error

import train_lstm as T

RAIN_THRESHOLD_MM = 1.0


def aligned_references():
    """Truth, persistence and monthly-climatology forecasts for exactly the
    test rows the LSTM predicts (global rows [test_start + WINDOW : end])."""
    df = T.load_frame()
    Y = df[T.TARGET_FEATURES].values.astype(float)  # physical units, precip in mm
    months = df["date"].dt.month.values

    n = len(df)
    n_tr, n_va = int(0.70 * n), int(0.15 * n)
    test_start = n_tr + n_va
    g = np.arange(test_start + T.WINDOW, n)

    truth = Y[g]
    persistence = Y[g - 1]

    train_idx = np.arange(0, n_tr)
    month_mean = np.vstack([
        Y[train_idx[months[train_idx] == m]].mean(axis=0)
        if (months[train_idx] == m).any() else Y[train_idx].mean(axis=0)
        for m in range(1, 13)
    ])
    climatology = month_mean[months[g] - 1]
    return truth, persistence, climatology


def lstm_predictions():
    data, _, scaler_y = T.prepare()
    model = tf.keras.models.load_model("best_lstm.keras", compile=False)
    Xte, yte = data["test"]
    hat = scaler_y.inverse_transform(model.predict(Xte, verbose=0)).copy()
    truth = scaler_y.inverse_transform(yte).copy()
    hat[:, -1] = np.expm1(hat[:, -1])
    truth[:, -1] = np.expm1(truth[:, -1])
    return hat, truth


def rain_skill(obs, pred, thr=RAIN_THRESHOLD_MM):
    o, p = obs >= thr, pred >= thr
    a = int((o & p).sum())    # hits
    b = int((~o & p).sum())   # false alarms
    c = int((o & ~p).sum())   # misses
    d = int((~o & ~p).sum())  # correct negatives
    pod = a / (a + c) if (a + c) else float("nan")
    far = b / (a + b) if (a + b) else float("nan")
    csi = a / (a + b + c) if (a + b + c) else float("nan")
    acc = (a + d) / (a + b + c + d)
    return pod, far, csi, acc, a + c


def main():
    hat, model_truth = lstm_predictions()
    truth, persistence, climatology = aligned_references()

    # The scaled/inverse-transformed truth must line up with the raw rows.
    assert np.allclose(model_truth, truth, atol=0.5), np.abs(model_truth - truth).max()

    preds = {"LSTM (improved)": hat, "Persistence": persistence, "Climatology": climatology}
    header = f"{'model':<18}" + "".join(f"{n:>10}" for n in T.TARGET_FEATURES) + f"{'overall':>10}"
    print("MAE by target (lower is better)")
    print(header)
    for name, pred in preds.items():
        per = [mean_absolute_error(truth[:, j], pred[:, j]) for j in range(len(T.TARGET_FEATURES))]
        overall = float(np.mean(np.abs(truth - pred)))
        print(f"{name:<18}" + "".join(f"{x:>10.3f}" for x in per) + f"{overall:>10.3f}")

    print(f"\nRain vs no-rain skill (threshold {RAIN_THRESHOLD_MM} mm)")
    print(f"{'model':<18}{'POD':>8}{'FAR':>8}{'CSI':>8}{'ACC':>8}{'rain days':>11}")
    for name in ("LSTM (improved)", "Persistence"):
        pod, far, csi, acc, events = rain_skill(truth[:, 3], preds[name][:, 3])
        print(f"{name:<18}{pod:>8.3f}{far:>8.3f}{csi:>8.3f}{acc:>8.3f}{events:>11d}")


if __name__ == "__main__":
    main()
