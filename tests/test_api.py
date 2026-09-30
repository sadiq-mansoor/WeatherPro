"""Endpoint tests for the public API surface."""


def test_home_lists_endpoints(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "available_endpoints" in body
    # Both current and forecast must be advertised
    endpoints_str = " ".join(body["available_endpoints"])
    assert "/api/current" in endpoints_str
    assert "/api/forecast" in endpoints_str


def test_health_reports_model_loaded(client):
    body = client.get("/health").get_json()
    assert body["status"] == "healthy"
    assert body["model_loaded"] is True
    assert body["scalers_loaded"] is True


def test_current_returns_prediction(client, module, sample_weather, monkeypatch):
    monkeypatch.setattr(module, "get_current_weather", lambda: sample_weather)
    body = client.get("/api/current").get_json()
    for key in ("temp_c", "temp_f", "wind_speed", "humidity", "rain_probability"):
        assert key in body, f"Missing key: {key}"


def test_current_survives_weather_outage(client, module, monkeypatch):
    # When the upstream API is down get_current_weather returns None;
    # the endpoint must still predict from the last known window, not crash.
    monkeypatch.setattr(module, "get_current_weather", lambda: None)
    resp = client.get("/api/current")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "temp_c" in body, "Prediction keys missing when weather API is down"


def test_forecast_returns_seven_days(client):
    body = client.get("/api/forecast").get_json()
    assert "forecast" in body
    assert len(body["forecast"]) == 7, (
        f"Expected 7 forecast days, got {len(body['forecast'])}"
    )
    assert all("timestamp" in day for day in body["forecast"])


def test_forecast_each_day_has_all_fields(client):
    body = client.get("/api/forecast").get_json()
    required = {"temp_c", "temp_f", "wind_speed", "humidity", "rain_probability", "timestamp"}
    for i, day in enumerate(body["forecast"]):
        missing = required - set(day.keys())
        assert not missing, f"Day {i} missing fields: {missing}"


def test_debug_predict_requires_admin_and_exposes_raw_output(client):
    unauthorized = client.get("/debug_predict")
    assert unauthorized.status_code == 401
    body = client.get(
        "/debug_predict",
        headers={"Authorization": "Bearer test-token"},
    ).get_json()
    assert "prediction" in body
    assert "raw_model_output" in body
    assert "inverse_transformed" in body
