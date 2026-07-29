# Test Plan

## Scope

Functional and non-functional testing of the Weather Forecast backend API and
the LSTM prediction pipeline. Frontend is validated manually (see checklist).

## Test cases

| ID | Area | Case | Expected | Automated |
|----|------|------|----------|-----------|
| API-01 | Health | `GET /health` | 200, `model_loaded` and `scalers_loaded` true | yes |
| API-02 | Home | `GET /` | 200, endpoint list returned | yes |
| API-03 | Current | `GET /api/current` with live data | Prediction with all 5 fields | yes |
| API-04 | Current | `GET /api/current` when weather API is down | Still 200, predicts from last window | yes |
| API-05 | Forecast | `GET /api/forecast` | 7 dated forecast entries | yes |
| API-06 | Debug | `GET /debug_predict` | Raw + inverse-transformed output present | yes |
| SEC-01 | Admin | `/api/admin/verify` with no token | 401 | yes |
| SEC-02 | Admin | `/api/admin/verify` with wrong token | 401 | yes |
| SEC-03 | Admin | `/api/admin/verify` with correct token | 200 | yes |
| SEC-04 | Admin | `/api/admin/window` and `/update` without token | 401 | yes |
| SEC-05 | Admin | Any admin route when `ADMIN_TOKEN` unset | 401 | yes |
| MOD-01 | Model | Input/output shape | `(30, 5) -> 4` | yes |
| MOD-02 | Model | Scaler feature counts | X=5, y=4 | yes |
| REP-01 | Repro | Same input twice | Identical output | yes |
| REP-02 | Repro | Output bounds | humidity 0-100, wind >=0, rain 0-100 | yes |
| REP-03 | Repro | Batch vs single prediction | Match | yes |

## Manual QA checklist (frontend)

- [ ] App loads and shows current weather for Peshawar.
- [ ] 7-day forecast renders with day labels and values.
- [ ] Admin login rejects an empty/incorrect token.
- [ ] Admin login succeeds with the configured token and reveals the panel.
- [ ] Logout returns to the login state.
- [ ] With the backend stopped, the UI degrades without crashing.

## Environment

- Python 3.11, TensorFlow 2.x, Flask.
- Model artifacts present in `backend/`.
- Run: `pytest` from `Test(QA)/`.
