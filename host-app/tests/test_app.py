"""Login validation and the rule that RLS comes only from the region whitelist."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.users import rls_rules


def test_rls_is_only_the_whitelisted_region() -> None:
    assert rls_rules("sara") == [{"clause": "region IN ('north')"}]
    assert rls_rules("office") == []
    assert "created_at" not in rls_rules("reza")[0]["clause"]


def test_unknown_region_is_rejected(monkeypatch) -> None:
    from app import users

    monkeypatch.setitem(users.USERS, "bad", {"display_name": "بد", "region": "secret' OR 1=1"})
    with pytest.raises(ValueError):
        users.rls_rules("bad")


@pytest.fixture
def client(tmp_path, monkeypatch):
    info = tmp_path / "embed.json"
    info.write_text(json.dumps({"slug": "sales-jalali", "uuid": "abc-123"}), encoding="utf-8")
    monkeypatch.setenv("EMBED_INFO_PATH", str(info))
    monkeypatch.setenv("HOST_APP_SECRET", "test-secret")
    monkeypatch.setenv("SUPERSET_PUBLIC_URL", "http://localhost:8100")
    monkeypatch.setenv("SUPERSET_INTERNAL_URL", "http://superset:8088")
    monkeypatch.setenv("GUEST_TOKEN_SERVICE_USERNAME", "guest_token_service")
    monkeypatch.setenv("GUEST_TOKEN_SERVICE_PASSWORD", "secret")
    from app import main

    monkeypatch.setattr(main, "_uuid", None)
    return TestClient(main.app)


def test_login_validation(client: TestClient) -> None:
    assert client.post("/api/login", json={"user": "no-such"}).status_code == 400
    ok = client.post("/api/login", json={"user": "sara"})
    assert ok.status_code == 200
    assert client.get("/api/session").json()["user"] == "sara"
    assert "host_app_session" in ok.headers["set-cookie"]


def test_guest_token_requires_a_session_and_builds_rls(client: TestClient, monkeypatch) -> None:
    assert client.get("/api/guest-token").status_code == 401
    client.post("/api/login", json={"user": "reza"})
    captured: dict = {}

    def fake_guest_token(**kwargs):
        captured.update(kwargs)
        return "jwt-demo"

    from app import main

    monkeypatch.setattr(main._client, "guest_token", fake_guest_token)
    response = client.get("/api/guest-token")
    assert response.status_code == 200
    assert response.json() == {"token": "jwt-demo"}
    assert captured["rls"] == [{"clause": "region IN ('south')"}]
    assert captured["dashboard_uuid"] == "abc-123"


def test_embed_config(client: TestClient) -> None:
    body = client.get("/api/embed-config").json()
    assert body == {"supersetDomain": "http://localhost:8100", "dashboardUuid": "abc-123"}
