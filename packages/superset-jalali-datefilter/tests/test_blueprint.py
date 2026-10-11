"""The plugin list must answer 200 for every caller."""

from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask, jsonify
from flask_login import LoginManager, UserMixin, login_user

blueprint_module = importlib.import_module("superset_jalali_datefilter.blueprint")


class User(UserMixin):
    def __init__(self, user_id: str = "1") -> None:
        self.id = user_id


@pytest.fixture
def static_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(blueprint_module, "STATIC_DIR", tmp_path)
    (tmp_path / "manifest.json").write_text(
        json.dumps({"file": "jalali-datefilter.abc.js", "hello": "hello.def.js", "version": "1.0.0"}),
        encoding="utf-8",
    )
    (tmp_path / "jalali-datefilter.abc.js").write_text("export {}", encoding="utf-8")
    (tmp_path / "hello.def.js").write_text("export {}", encoding="utf-8")
    return tmp_path


def _app(static_dir, *, authenticated: bool = False) -> Flask:
    del static_dir, authenticated
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    login_manager = LoginManager(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User:
        return User(user_id)

    app.register_blueprint(blueprint_module.blueprint)

    @app.route("/__login")
    def _login():
        login_user(User())
        return "ok"

    return app


def test_anonymous_is_empty_and_not_cached(static_dir) -> None:
    client = _app(static_dir).test_client()
    response = client.get("/dynamic-plugins/api/read")
    assert response.status_code == 200
    assert response.get_json() == {"result": []}
    assert response.headers["Cache-Control"] == "no-store"


def test_authenticated_lists_the_bundle(static_dir) -> None:
    app = _app(static_dir)
    client = app.test_client()
    client.get("/__login")
    response = client.get("/dynamic-plugins/api/read")
    assert response.status_code == 200
    body = response.get_json()["result"]
    assert body[0]["key"] == "jalali-datefilter"
    assert body[0]["bundle_url"] == "/jalali-datefilter/static/jalali-datefilter.abc.js"


def test_application_root_and_hello_bundle(static_dir) -> None:
    app = _app(static_dir)
    app.config["APPLICATION_ROOT"] = "/bi"
    app.config["JALALI_DATEFILTER"] = {"enabled": True, "bundle": "hello"}
    client = app.test_client()
    client.get("/__login")
    response = client.get("/dynamic-plugins/api/read")
    assert response.get_json()["result"][0]["bundle_url"] == "/bi/jalali-datefilter/static/hello.def.js"


def test_disabled_is_empty(static_dir) -> None:
    app = _app(static_dir)
    app.config["JALALI_DATEFILTER"] = {"enabled": False}
    client = app.test_client()
    client.get("/__login")
    assert client.get("/dynamic-plugins/api/read").get_json() == {"result": []}


def test_list_never_fails(static_dir, monkeypatch) -> None:
    def explode():
        raise RuntimeError("manifest missing")

    monkeypatch.setattr(blueprint_module, "bundle_url", explode)
    app = _app(static_dir)
    client = app.test_client()
    client.get("/__login")
    response = client.get("/dynamic-plugins/api/read")
    assert response.status_code == 200
    assert response.get_json() == {"result": []}


def test_static_is_immutable(static_dir) -> None:
    client = _app(static_dir).test_client()
    response = client.get("/jalali-datefilter/static/jalali-datefilter.abc.js")
    assert response.status_code == 200
    assert "immutable" in response.headers["Cache-Control"]


def test_health(static_dir) -> None:
    response = _app(static_dir).test_client().get("/jalali-datefilter/health")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert response.get_json()["bundle"] == "jalali-datefilter.abc.js"


def test_duplicate_route_is_left_alone(static_dir) -> None:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    LoginManager(app)

    def upstream():
        return jsonify(result=["upstream"])

    app.add_url_rule("/dynamic-plugins/api/read", endpoint="upstream", view_func=upstream)
    app.register_blueprint(blueprint_module.blueprint)
    response = app.test_client().get("/dynamic-plugins/api/read")
    assert response.get_json() == {"result": ["upstream"]}
