"""Access control tests for the /api/admin/* endpoints."""

TOKEN = "test-token"


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── /api/admin/verify ──────────────────────────────────────────────────────────

def test_verify_rejects_missing_header(client):
    assert client.post("/api/admin/verify").status_code == 401


def test_verify_rejects_wrong_token(client):
    assert client.post("/api/admin/verify", headers=auth("nope")).status_code == 401


def test_verify_accepts_correct_token(client):
    resp = client.post("/api/admin/verify", headers=auth(TOKEN))
    assert resp.status_code == 200
    assert resp.get_json()["authorized"] is True


# ── /api/admin/window ─────────────────────────────────────────────────────────

def test_window_requires_auth(client):
    assert client.get("/api/admin/window").status_code == 401


def test_window_accessible_with_token(client):
    resp = client.get("/api/admin/window", headers=auth(TOKEN))
    assert resp.status_code == 200
    data = resp.get_json()
    # Should be a 30×5 list of lists
    assert isinstance(data, list)
    assert len(data) == 30
    assert all(len(row) == 5 for row in data)


# ── /api/admin/update ─────────────────────────────────────────────────────────

def test_update_requires_auth(client):
    payload = [[0.0] * 5 for _ in range(30)]
    assert client.post("/api/admin/update", json=payload).status_code == 401


def test_update_accepts_correct_shape(client):
    payload = [[0.0] * 5 for _ in range(30)]
    resp = client.post("/api/admin/update", json=payload, headers=auth(TOKEN))
    assert resp.status_code == 200


def test_update_rejects_wrong_shape(client):
    # 10 rows × 5 cols — should be rejected with 400
    bad_payload = [[0.0] * 5 for _ in range(10)]
    resp = client.post("/api/admin/update", json=bad_payload, headers=auth(TOKEN))
    assert resp.status_code == 400
    assert "shape" in resp.get_json().get("error", "").lower()


def test_update_rejects_missing_body(client):
    resp = client.post(
        "/api/admin/update",
        data="",
        content_type="application/json",
        headers=auth(TOKEN),
    )
    assert resp.status_code == 400


def test_update_rejects_non_finite_values(client):
    payload = [[0.0] * 5 for _ in range(30)]
    payload[0][0] = float("nan")
    resp = client.post("/api/admin/update", json=payload, headers=auth(TOKEN))
    assert resp.status_code == 400


# ── /api/admin/history ────────────────────────────────────────────────────────

def test_history_requires_auth(client):
    assert client.get("/api/admin/history").status_code == 401


def test_history_accessible_with_token(client):
    resp = client.get("/api/admin/history", headers=auth(TOKEN))
    assert resp.status_code == 200
    body = resp.get_json()
    assert "total_rows" in body
    assert "history" in body
    assert "features" in body
    assert len(body["features"]) == 5


# ── Admin disabled when ADMIN_TOKEN is unset ──────────────────────────────────

def test_admin_disabled_when_token_unset(client, module, monkeypatch):
    # With no ADMIN_TOKEN configured, every admin route must stay locked
    # even if the caller sends a bearer token.
    monkeypatch.setattr(module, "ADMIN_TOKEN", None)
    assert client.post("/api/admin/verify", headers=auth(TOKEN)).status_code == 401
    assert client.get("/api/admin/window", headers=auth(TOKEN)).status_code == 401
    assert client.get("/api/admin/history", headers=auth(TOKEN)).status_code == 401
