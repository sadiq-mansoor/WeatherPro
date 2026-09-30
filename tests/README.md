# Test / QA

Automated tests and QA material for the Weather Forecast app. The suite covers
the Flask API, admin access control, the model/scaler contract, and prediction
reproducibility.

## Layout

| File | What it checks |
|------|----------------|
| `test_api.py` | Public endpoints and the protected `/debug_predict` endpoint, including behaviour when the upstream weather API is unavailable |
| `test_admin_auth.py` | Bearer-token auth on `/api/admin/*`, and that admin is fully disabled when `ADMIN_TOKEN` is unset |
| `test_model_contract.py` | Model I/O shape `(30, 5) -> 4` and matching scaler feature counts |
| `test_reproducibility.py` | Deterministic inference, physical output ranges, batch/single agreement, pinned training seed |
| `TEST_PLAN.md` | Test cases and manual QA checklist |
| `results/model_metrics.md` | Held-out test metrics from the latest training run |

## Running

From the repository root:

```bash
python -m pip install -r backend/requirements.txt
python -m pip install -r tests/requirements-test.txt
python -m pytest -q tests
```

The tests import the backend app, which loads `best_lstm.keras` and the scalers,
so the model artifacts must be present in `../backend/`. `ADMIN_TOKEN` is set to
a throwaway value automatically in `conftest.py`.

## Reproducing the model results

Training is seeded (`SEED = 42`) and the data split is chronological, so metrics
are reproducible. See `results/model_metrics.md` for the numbers and the exact
command.
