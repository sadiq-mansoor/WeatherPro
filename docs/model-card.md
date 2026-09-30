# Model Card — Peshawar Weather LSTM

## Overview

| Property | Value |
|----------|-------|
| Model type | Stacked LSTM (recurrent neural network) |
| Task | Multi-output next-day weather regression |
| Location | Peshawar, Pakistan (34.01°N, 71.58°E) |
| Input | 30-day rolling window × 5 weather features |
| Output | Next-day temperature, humidity, wind speed, precipitation |
| Training period | 2000–2024 daily records |
| Developed at | NCAI, UET Peshawar (CISNR) |

---

## Intended use

This model is designed to forecast **next-day weather conditions for Peshawar** as part of a research and demonstration application at NCAI, UET Peshawar. It is suitable for:

- Academic demonstration of applied deep learning in weather forecasting
- Public-facing weather apps for Peshawar residents
- Baseline comparison for future improved models

It is **not** intended as a replacement for operational meteorological forecasts from official agencies (PMD — Pakistan Meteorological Department).

---

## Architecture

```
Input layer:   (batch_size, 30, 5)
LSTM layer 1:  128 units, return_sequences=True
Dropout:       0.15
LSTM layer 2:  64 units
Dropout:       0.15
Dense:         32 units, ReLU activation
Output:        4 units, linear activation
               [temp_f, humidity, wind_speed, precip_log1p]
```

**Parameters:** ~135,000 trainable weights

---

## Training

### Dataset

| Property | Detail |
|----------|--------|
| Records | 5,114 daily rows |
| Date range | 2000–2024 |
| Location | Peshawar, Pakistan |
| Primary source | NCAI on-site weather sensors (CISNR, UET Peshawar) |
| Supplementary | Pakistan weather open dataset (Kaggle), Visual Crossing |

### Data split (chronological — no shuffling)

| Split | Rows | Percentage |
|-------|------|------------|
| Train | 3,549 | 70 % |
| Validation | 737 | 15 % |
| Test | 738 | 15 % |

Scalers (`MinMaxScaler`) are fit on the **training split only**. No test-set statistics leak into training.

### Input features

| Feature | Unit | Description |
|---------|------|-------------|
| pressure | hPa | Atmospheric pressure |
| dew_point_f | °F | Dew point temperature |
| humidity | % | Relative humidity |
| wind_speed | m/s | Wind speed |
| temp_f | °F | Air temperature |

### Target features

| Feature | Unit | Notes |
|---------|------|-------|
| temp_f | °F | Next-day air temperature |
| humidity | % | Next-day relative humidity |
| wind_speed | m/s | Next-day wind speed |
| precip | mm | Log1p-transformed at training; expm1 applied at inference |

### Hyperparameters

| Parameter | Value |
|-----------|-------|
| Sequence window | 30 days |
| Epochs (max) | 120 |
| Batch size | 32 |
| Loss function | MAE |
| Optimizer | Adam (lr=0.001, clipnorm=1.0) |
| Early stopping patience | 15 epochs |
| LR scheduler | ReduceLROnPlateau (patience=6, factor=0.5) |
| Random seed | 42 |

---

## Evaluation — legacy reference results

The numbers below are historical reference results from the earlier pipeline.
They must be regenerated after the current validation-only selection protocol
is run on the approved dataset. They should not be presented as the current
certified unseen-data score until that rerun is complete.

### Regression metrics (lower is better)

| Target | MAE | RMSE |
|--------|-----|------|
| Temperature (°F) | 1.670 | 2.285 |
| Humidity (%) | 5.340 | 7.366 |
| Wind speed | 1.886 | 2.673 |
| Precipitation (mm) | 1.537 | 5.189 |
| **Overall MAE** | **2.608** | — |

### Comparison against baselines

| Model | Overall MAE | vs. LSTM |
|-------|-------------|----------|
| **LSTM (this model)** | **2.608** | — |
| Persistence ("tomorrow = today") | 3.229 | +23.8 % higher |
| Climatology (monthly average) | 4.717 | +81.0 % higher |

The LSTM beats the persistence baseline on **every target** (~19 % lower overall MAE).

### Precipitation as a rain / no-rain event (threshold: 1 mm)

| Model | POD | FAR | CSI | Accuracy |
|-------|-----|-----|-----|----------|
| LSTM | 0.400 | 0.365 | 0.325 | 0.848 |
| Persistence | 0.496 | 0.504 | 0.330 | 0.816 |

Rain detection is the honest weak point. The LSTM and persistence are roughly tied on CSI — the LSTM detects fewer rain days but raises fewer false alarms and is more accurate overall. Precipitation timing at daily resolution from a single station is inherently difficult.

---

## Limitations

1. **Single station** — trained only on Peshawar city data; not applicable to other locations without retraining.
2. **Precipitation is the weakest output** — a single-station daily model cannot reliably predict rain timing.
3. **Single training run** — metrics are from one run (seed 42). No multi-seed mean ± std reported.
4. **Daily resolution** — hourly patterns are not captured.
5. **No external NWP features** — the model uses only local observations, not numerical weather prediction outputs.

---

## Reproducing results

```bash
# From the backend/ directory, with training data present:
python train_lstm.py

# To compare against baselines:
python evaluate_baselines.py
```

See `tests/results/model_metrics.md` for the legacy reference numbers and the
current rerun instructions.

---

## Version history

| Version | Description |
|---------|-------------|
| v1 (baseline) | Original notebook — scalers fit on full dataset (data leakage present) |
| v2 (improved) | Fixed data leakage; switched loss to MAE; Magnus dew-point formula |
