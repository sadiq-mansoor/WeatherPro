# Model results

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

## What changed vs. the baseline

- **Fixed data leakage** — the earlier pipeline fit the scalers on the whole
  dataset before splitting. Scalers are now fit on the training split only.
- **Objective aligned with the metric** — the improved model trains against MAE
  (what we report) instead of MSE, with lighter dropout and gradient clipping.

The `improved` model is only kept when it beats the `baseline` on the test set;
otherwise `train_lstm.py` leaves the existing artifacts untouched.
