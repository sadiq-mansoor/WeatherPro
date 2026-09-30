# API Reference

Base URL: `http://localhost:5000` (local) or your deployed backend URL.

All responses are JSON. Timestamps are UTC ISO-8601 strings.

---

## Public endpoints

These endpoints require no authentication.

---

### `GET /`

Returns the API status and a list of all available endpoints.

**Response**

```json
{
  "message": "Weather Prediction API — NCAI, UET Peshawar",
  "status": "running",
  "available_endpoints": [
    "GET  /health",
    "GET  /api/current",
    "GET  /api/forecast",
    "GET  /debug_predict (admin)",
    "POST /api/admin/verify",
    "GET  /api/admin/window",
    "POST /api/admin/update",
    "GET  /api/admin/history"
  ]
}
```

---

### `GET /health`

Liveness and readiness check. Returns 200 when the model and scalers are loaded.

**Response**

```json
{
  "status": "healthy",
  "timestamp": "2026-10-01T08:00:00Z",
  "model_loaded": true,
  "scalers_loaded": true
}
```

---

### `GET /api/current`

Fetches live weather data from OpenWeatherMap, advances the 30-day rolling window, and returns the model's prediction for **current conditions**.

If the upstream weather API is unavailable, the endpoint predicts from the last known window rather than returning an error.

**Response**

```json
{
  "temp_c": 34.5,
  "temp_f": 94.1,
  "humidity": 42.0,
  "wind_speed": 3.2,
  "rain_probability": 5.4
}
```

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `temp_c` | float | °C | Predicted temperature |
| `temp_f` | float | °F | Predicted temperature |
| `humidity` | float | % (0–100) | Predicted relative humidity |
| `wind_speed` | float | m/s | Predicted wind speed |
| `rain_probability` | float | % (0–100) | Predicted rain probability |

**Error response (500)**

```json
{ "error": "description of what went wrong" }
```

---

### `GET /api/forecast`

Returns a **7-day autoregressive forecast**. Each step uses the previous step's predictions as the next input window row, so the forecast genuinely diverges over time.

**Response**

```json
{
  "forecast": [
    {
      "temp_c": 35.1,
      "temp_f": 95.2,
      "humidity": 40.0,
      "wind_speed": 3.5,
      "rain_probability": 4.2,
      "timestamp": "2026-10-01T12:00:00Z"
    },
    {
      "temp_c": 34.8,
      "temp_f": 94.6,
      "humidity": 41.5,
      "wind_speed": 3.3,
      "rain_probability": 6.1,
      "timestamp": "2026-10-02T12:00:00Z"
    }
  ]
}
```

Each object in `forecast` has the same fields as `/api/current` plus a `timestamp` (UTC, one per day).

---

### `GET /debug_predict` (admin)

Exposes the raw model outputs for debugging and inspection. This endpoint
requires the same Bearer token as the admin endpoints. Shows both the scaled
(model-space) values and the inverse-transformed (physical-unit) values.

**Response**

```json
{
  "prediction": {
    "temp_c": 34.5,
    "temp_f": 94.1,
    "humidity": 42.0,
    "wind_speed": 3.2,
    "rain_probability": 5.4
  },
  "raw_model_output": [0.62, 0.41, 0.18, 0.03],
  "inverse_transformed": [94.1, 42.0, 3.2, 0.031]
}
```

---

## Admin endpoints

All admin endpoints require a `Bearer` token in the `Authorization` header.

```
Authorization: Bearer <ADMIN_TOKEN>
```

If `ADMIN_TOKEN` is not set on the server, **all admin endpoints return 401** regardless of what token is sent. This is intentional — the admin panel is fully disabled by default.

The debug endpoint is also protected by this rule.

---

### `POST /api/admin/verify`

Validates an admin token. Use this before showing the admin UI to confirm the token is accepted.

**Headers**

```
Authorization: Bearer <token>
```

**Response (200 — valid token)**

```json
{ "authorized": true }
```

**Response (401 — invalid or missing token)**

```json
{ "error": "Unauthorized" }
```

---

### `GET /api/admin/window`

Returns the current 30×5 rolling prediction window — the last 30 days of feature readings the model uses as context.

**Response**

```json
[
  [1013.0, 58.2, 45.0, 3.1, 86.4],
  [1012.5, 57.8, 44.0, 2.9, 87.1],
  "... 28 more rows ..."
]
```

Each row contains: `[pressure_hPa, dew_point_f, humidity_pct, wind_speed_ms, temp_f]`

---

### `POST /api/admin/update`

Replaces the rolling prediction window. Useful for testing, correcting stale data, or manually seeding the model with known-good conditions.

**Body** — a JSON array with exactly 30 rows and 5 columns:

```json
[
  [1013.0, 58.2, 45.0, 3.1, 86.4],
  [1012.5, 57.8, 44.0, 2.9, 87.1],
  "... 28 more rows ..."
]
```

**Response (200)**

```json
{ "message": "Window updated successfully" }
```

**Response (400 — wrong shape)**

```json
{ "error": "Invalid window shape (10, 5). Expected (30, 5)." }
```

---

### `GET /api/admin/history`

Returns the accumulated history of sensor feature readings (up to the last 200 rows).

**Response**

```json
{
  "total_rows": 480,
  "rows_returned": 200,
  "features": ["pressure", "dew_point_f", "humidity", "wind_speed", "temp_f"],
  "history": [
    [1013.0, 58.2, 45.0, 3.1, 86.4],
    "..."
  ]
}
```

---

## Error codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (missing or malformed body) |
| 401 | Unauthorized (missing, wrong, or disabled admin token) |
| 500 | Internal server error (check the configured runtime log for details) |
