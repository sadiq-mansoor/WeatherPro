# Peshawar Weather Forecast

An LSTM based weather forecasting service for Peshawar, Pakistan. The project
contains a Flask API, a React web app, model artifacts, training code, tests,
and deployment configuration.

## Current status

The local backend inference path is implemented and covered by 30 automated
tests. The frontend source and production build configuration are present.
Live deployment still requires hosting accounts, environment variables, and a
deployment run; no live URL is claimed by this repository.

## Repository layout

```text
api/           Vercel Python Function entrypoint for the Flask API
backend/       Flask API, training/evaluation scripts, inference artifacts
frontend/      React single-page application
data/          Dataset instructions; large source files stay outside Git
docs/          API, model, deployment, and contribution guides
tests/         Backend tests and reference evaluation results
render.yaml    Render web-service configuration
vercel.json    Vercel frontend configuration
```

## Local setup

### Backend

Requirements: Python 3.11 and an OpenWeatherMap API key.

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set OPENWEATHER_API_KEY.
python app.py
```

The API starts at `http://localhost:5000`. The checked-in model artifacts are
loaded automatically. If they are missing, the API stops with a clear error.

### Frontend

```powershell
cd frontend
npm ci
npm start
```

The web app starts at `http://localhost:3000` and proxies API requests to the
local backend. For a single-project Vercel deployment, leave
`REACT_APP_API_URL` empty so the browser uses the same-origin serverless API.
Set it only when the backend is deployed separately.

## Configuration

Backend variables are documented in [backend/.env.example](backend/.env.example).
The important variables are:

| Variable                                             |             Required | Purpose                            |
| ---------------------------------------------------- | -------------------: | ---------------------------------- |
| `OPENWEATHER_API_KEY`                              | Yes for live weather | OpenWeatherMap API key             |
| `ADMIN_TOKEN`                                      |                   No | Enables protected admin operations |
| `CORS_ORIGINS`                                     |           Production | Comma-separated frontend origins   |
| `WEATHER_DATA_DIR`                                 |                   No | Runtime state and logs directory   |
| `MODEL_PATH`, `SCALER_X_PATH`, `SCALER_Y_PATH` |                   No | Override artifact locations        |

Leave `ADMIN_TOKEN` empty to keep admin operations disabled. Set
`CORS_ORIGINS` to the exact frontend origin in production.

## API

See [docs/api-reference.md](docs/api-reference.md). The main endpoints are:

| Method   | Endpoint               | Access                    |
| -------- | ---------------------- | ------------------------- |
| GET      | `/health`            | Public readiness check    |
| GET      | `/api/current`       | Public current prediction |
| GET      | `/api/forecast`      | Public seven-day forecast |
| POST     | `/api/admin/verify`  | Admin token required      |
| GET/POST | `/api/admin/window`  | Admin token required      |
| GET      | `/api/admin/history` | Admin token required      |
| GET      | `/debug_predict`     | Admin token required      |

The model predicts temperature, humidity, wind speed, and precipitation. The
API exposes precipitation as a bounded rain-probability display value for the
existing UI; it is a proxy, not a calibrated probability.

## Training and evaluation

Training data is not committed because of its size and source licensing. Read
[data/README.md](data/README.md) before training. The expected CSV path is:

```text
data/raw/peshawar_weather_2000_2024.csv
```

Then run:

```powershell
cd backend
python audit_dataset.py
python train_lstm.py
python evaluate_baselines.py
```

The training script validates the file and required columns before doing any
work. It fits scalers on the training split only and writes artifacts into
`backend/`.

Legacy reference metrics are recorded in
[tests/results/model_metrics.md](tests/results/model_metrics.md). They must be
regenerated with the approved dataset after any pipeline change before being
used as current performance claims.

## Testing

```powershell
python -m pip install -r backend/requirements.txt
python -m pip install -r tests/requirements-test.txt
python -m pytest -q tests
```

The CI workflow runs the backend tests and the frontend production build:
[.github/workflows/test.yml](.github/workflows/test.yml).

## Deployment

- Vercel: import the repository root, use the checked-in `vercel.json`, and
  set the serverless API secrets documented in [docs/deployment.md](docs/deployment.md).
- Render: use the checked-in `render.yaml`, then set the secret values in the
  Render dashboard.

Read [docs/deployment.md](docs/deployment.md) for the complete checklist and
post-deployment verification commands.

## Limitations

- The model is trained for Peshawar and should not be presented as a general
  weather model.
- Rain output is the weakest model target and is not a calibrated probability.
- Runtime state is file-backed and should use persistent storage for a hosted
  service.
- Model metrics are from the documented evaluation run and require the source
  dataset to reproduce.

## License

MIT. See [LICENSE](LICENSE).
