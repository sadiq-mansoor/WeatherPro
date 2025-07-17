"""Access control tests for the /api/admin/* endpoints."""

TOKEN = "test-token"


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_verify_rejects_missing_header(client):
    assert client.post("/api/admin/verify").status_code == 401


def test_verify_rejects_wrong_token(client):
    assert client.post("/api/admin/verify", headers=auth("nope")).status_code == 401


def test_verify_accepts_correct_token(client):
    resp = client.post("/api/admin/verify", headers=auth(TOKEN))
    assert resp.status_code == 200
    assert resp.get_json()["authorized"] is True


def test_window_requires_auth(client):
    assert client.get("/api/admin/window").status_code == 401
    assert client.get("/api/admin/window", headers=auth(TOKEN)).status_code == 200


def test_update_requires_auth(client):
    payload = [[0.0] * 5 for _ in range(30)]
    assert client.post("/api/admin/update", json=payload).status_code == 401
    ok = client.post("/api/admin/update", json=payload, headers=auth(TOKEN))
    assert ok.status_code == 200


def test_admin_disabled_when_token_unset(client, module, monkeypatch):
    # With no ADMIN_TOKEN configured, every admin route must stay locked even
    # if the caller sends a bearer token.
    monkeypatch.setattr(module, "ADMIN_TOKEN", None)
    assert client.post("/api/admin/verify", headers=auth(TOKEN)).status_code == 401
    assert client.get("/api/admin/window", headers=auth(TOKEN)).status_code == 401
