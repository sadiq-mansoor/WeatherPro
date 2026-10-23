# Deployment guide

The default deployment is a single Vercel project. React is served as static
files and the Flask API runs through the Vercel Python Function at
`api/index.py`. The API keeps only temporary rolling state because Vercel
Functions have a read-only deployment filesystem and instances can restart.
Render remains available for a persistent long-running backend when durable
history or predictable warm process performance is required.

## Before deploying

1. Ensure `backend/best_lstm.keras`, `backend/scaler_X.pkl`, and
   `backend/scaler_y.pkl` are available to the deployment checkout.
2. Run the backend tests locally.
3. Run `npm ci` and `npm run build` from `frontend/`.
4. Generate a strong `ADMIN_TOKEN`. Never commit it.

## Full application on Vercel

Import the repository using the repository root as the project root. The
checked-in `vercel.json` installs the React dependencies, builds
`frontend/`, serves `frontend/build/`, and routes `/api/*` to the Python
function.

Set these Vercel environment variables:

| Name | Required | Value |
|---|---|---|
| `OPENWEATHER_API_KEY` | Yes | OpenWeatherMap API key |
| `ADMIN_TOKEN` | Recommended | Strong secret for admin routes |
| `CORS_ORIGINS` | Optional | The Vercel origin; same-origin calls work without it |
| `VERCEL_SUPPORT_LARGE_FUNCTIONS` | If requested by Vercel | `1` for TensorFlow bundles over the standard size limit |
| `REACT_APP_API_URL` | No | Leave empty for the same-project API |

Redeploy after changing environment variables. Verify the deployed page loads
and browser requests reach `/api/current` and `/api/forecast`.

The Python runtime loads the small checked-in inference artifacts from
`backend/`. It writes rolling state and logs to the platform temporary
directory. That state is instance-local and can disappear after a cold start.
Do not use the Vercel function for model training or durable data collection.

## Optional persistent backend on Render

The checked-in `render.yaml` defines the service:

```text
Build:  pip install -r backend/requirements.txt
Start:  gunicorn --chdir backend --bind 0.0.0.0:$PORT app:app
Health: /health
```

Set these secret/environment variables in Render:

| Name | Required | Value |
|---|---:|---|
| `OPENWEATHER_API_KEY` | Yes | OpenWeatherMap API key |
| `ADMIN_TOKEN` | Recommended | Strong secret for admin routes |
| `CORS_ORIGINS` | Yes | Exact Vercel origin, for example `https://app.example.com` |
| `WEATHER_DATA_DIR` | Recommended | Persistent mount such as `/data` |

If a persistent disk is used, configure `WEATHER_DATA_DIR=/data`. The model
paths can remain at their defaults when the model files are part of the
deployment checkout. If the model files are mounted separately, set
`MODEL_PATH`, `SCALER_X_PATH`, and `SCALER_Y_PATH` explicitly.

## Post-deployment verification

Run these checks against the deployed Vercel URL:

```powershell
curl https://your-project.vercel.app/health
curl https://your-project.vercel.app/api/current
curl https://your-project.vercel.app/api/forecast
```

The health response must report `200`, `model_loaded: true`, and
`scalers_loaded: true`. Then load the real frontend and verify current weather,
forecast cards, admin login, window loading, window validation, and logout.

## Operational requirements

- Use HTTPS for both services.
- Restrict `CORS_ORIGINS` to the frontend origin.
- Keep the admin token in the hosting provider's secret store.
- Use persistent storage for `window.npy`, `history.npy`, and logs if state must
  survive restarts.
- Treat `/debug_predict` as an admin-only diagnostic endpoint.
- Re-run the health and API checks after every deployment.
