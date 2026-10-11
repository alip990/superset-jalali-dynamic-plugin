"""Replace the dynamic-plugin list route that Flask-AppBuilder 5 removed.

The list endpoint must never fail. A 4xx/5xx leaves DYNAMIC_PLUGINS loading
forever and every dashboard spins.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import Blueprint, current_app, jsonify, send_from_directory
from flask_login import current_user

logger = logging.getLogger(__name__)

PLUGIN_KEY = "jalali-datefilter"
STATIC_DIR = Path(__file__).resolve().parent / "static"
blueprint = Blueprint("jalali_datefilter", __name__)


def _nostore(response):
    response.headers["Cache-Control"] = "no-store"
    return response


def _settings() -> dict:
    return current_app.config.get("JALALI_DATEFILTER") or {}


def _enabled() -> bool:
    return bool(_settings().get("enabled", True))


def _manifest() -> dict:
    return json.loads((STATIC_DIR / "manifest.json").read_text(encoding="utf-8"))


def bundle_filename() -> str:
    manifest = _manifest()
    mode = _settings().get("bundle", "main")
    return manifest["hello"] if mode == "hello" else manifest["file"]


def bundle_url() -> str:
    root = current_app.config.get("APPLICATION_ROOT") or ""
    prefix = "" if root in ("", "/") else str(root).rstrip("/")
    return f"{prefix}/jalali-datefilter/static/{bundle_filename()}"


def plugin_list():
    try:
        if not current_user.is_authenticated or not _enabled():
            return _nostore(jsonify(result=[]))
        return _nostore(
            jsonify(
                result=[
                    {
                        "id": 1,
                        "name": "Jalali date filter",
                        "key": PLUGIN_KEY,
                        "bundle_url": bundle_url(),
                    }
                ]
            )
        )
    except Exception:
        current_app.logger.exception("jalali-datefilter: plugin list failed")
        return _nostore(jsonify(result=[]))


def static_file(filename: str):
    response = send_from_directory(STATIC_DIR, filename)
    if filename.endswith((".js", ".js.map", ".map")):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


def health():
    bundle = None
    present = False
    try:
        bundle = bundle_filename()
        present = (STATIC_DIR / bundle).is_file()
    except Exception:
        current_app.logger.exception("jalali-datefilter: health check failed")
    return jsonify(
        ok=present,
        bundle=bundle,
        enabled=_enabled(),
        version=_settings().get("version", "1.0.0"),
    )


def _has_rule(app, rule: str) -> bool:
    target = rule.rstrip("/") or "/"
    return any(existing.rule.rstrip("/") == target for existing in app.url_map.iter_rules())


@blueprint.record_once
def _mount(state) -> None:
    app = state.app
    if _has_rule(app, "/dynamic-plugins/api/read"):
        app.logger.warning(
            "jalali-datefilter: /dynamic-plugins/api/read is already registered; not replacing it"
        )
    else:
        app.add_url_rule(
            "/dynamic-plugins/api/read",
            endpoint="jalali_datefilter.plugin_list",
            view_func=plugin_list,
            methods=["GET"],
        )
    app.add_url_rule(
        "/jalali-datefilter/static/<path:filename>",
        endpoint="jalali_datefilter.static_file",
        view_func=static_file,
        methods=["GET"],
    )
    app.add_url_rule(
        "/jalali-datefilter/health",
        endpoint="jalali_datefilter.health",
        view_func=health,
        methods=["GET"],
    )
