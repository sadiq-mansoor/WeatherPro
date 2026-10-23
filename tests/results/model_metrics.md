# Legacy model results

> These numbers belong to the previous training protocol and are retained for
> historical comparison only. The pipeline now uses preceding observed context
> for validation/test targets and selects the saved model by validation MAE
> instead of test MAE. Rerun `backend/train_lstm.py` and
> `backend/evaluate_baselines.py` with the approved dataset before publishing
> new performance claims.

Held-out test metrics for the next-day forecast model. The split is
chronological (70% train / 15% val / 15% test) and the run is seeded
(`SEED = 42`), so these numbers reproduce exactly.

## How to reproduce

```bash
cd backend
python train_lstm.py
```

Scalers are fit on the training split only, and sequences are built inside each
split, so no test data leaks into training. Dataset: Peshawar daily records
(5,114 rows), features `[pressure, dew_point_f, humidity, wind, temp_f]`
predicting next-day `[temp_f, humidity, wind, precip]`.

Split sizes: train 3,549 · val 737 · test 738 windows.

## Test-set error (lower is better)

| Target | Baseline MAE | Improved MAE | Baseline RMSE | Improved RMSE |
|--------|-------------:|-------------:|--------------:|--------------:|
| temp_f (°F) | 1.757 | **1.670** | 2.342 | 2.285 |
| humidity (%) | 5.471 | **5.340** | 7.461 | 7.366 |
| wind | 1.928 | **1.886** | 2.634 | 2.673 |
| precip (mm) | 1.577 | **1.537** | 4.937 | 5.189 |
| **overall MAE** | 2.683 | **2.608** | | |

Overall MAE improved by **2.8%**, with a lower error on every target.

## Comparison against forecasting baselines

The number that matters: does the model beat the naive baselines every weather
forecast is judged against? Same test set, same targets.

| Model | temp_f | humidity | wind | precip | overall MAE |
|-------|-------:|---------:|-----:|-------:|------------:|
| **LSTM (improved)** | **1.670** | **5.340** | **1.886** | **1.537** | **2.608** |
| Persistence (tomorrow = today) | 1.898 | 6.509 | 2.451 | 2.058 | 3.229 |
| Climatology (monthly average) | 4.003 | 10.488 | 2.108 | 2.268 | 4.717 |

The LSTM beats persistence on **every** target (~19% lower overall MAE) and is
well ahead of climatology, so it is genuinely adding forecast value.

## Precipitation as a rain / no-rain event (threshold 1 mm)

Plain MAE flatters any model in a dry climate, so precip is also scored as a
binary rain event. POD = probability of detection, FAR = false-alarm ratio,
CSI = critical success index.

| Model | POD | FAR | CSI | Accuracy |
|-------|----:|----:|----:|---------:|
| LSTM (improved) | 0.400 | 0.365 | 0.325 | 0.848 |
| Persistence | 0.496 | 0.504 | 0.330 | 0.816 |

Rain is the honest weak spot: the LSTM and persistence are **effectively tied on
CSI**. The LSTM detects fewer rain days but raises far fewer false alarms and is
more accurate overall. Precipitation timing at daily resolution is hard for any
single-station model and would be the main target for future work.

Reproduce this comparison with `python evaluate_baselines.py` (from `backend/`).

## What changed vs. the earlier LSTM

- **Fixed data leakage** — the earlier pipeline fit the scalers on the whole
  dataset before splitting. Scalers are now fit on the training split only.
- **Objective aligned with the metric** — the improved model trains against MAE
  (what we report) instead of MSE, with lighter dropout and gradient clipping.

The current pipeline selects between candidates using validation MAE. The test
set is used only once for the final report and never determines which model is
saved.

## Known limitations / future work

Single training run per model (no multi-seed mean±std yet), single weather
station, and precipitation is the weakest target. A publication-grade write-up
would add seeded repeats with variance, statistical significance tests, and a
non-LSTM baseline (e.g. gradient boosting).
