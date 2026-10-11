"""Superset configuration. Secrets come from the environment; nothing is hardcoded."""

from __future__ import annotations

import os

# Imported while superset.config is loading this module. The names we read are
# already bound. Star-import then replaces THEME_* and TALISMAN_CONFIG.
from superset.config import (  # type: ignore
    CORS_OPTIONS as _CORS_OPTIONS,
    TALISMAN_CONFIG as _TALISMAN_CONFIG,
    THEME_DARK as _THEME_DARK,
    THEME_DEFAULT as _THEME_DEFAULT,
)

from superset_jalali_datefilter import blueprint as jalali_datefilter_bp
from superset_jalali_sql import JINJA_ADDONS


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"missing required environment variable {name}")
    return value


def env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _redis(prefix: str, timeout: int) -> dict:
    return {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": timeout,
        "CACHE_KEY_PREFIX": prefix,
        "CACHE_REDIS_URL": env("REDIS_URL"),
    }


SECRET_KEY = env("SUPERSET_SECRET_KEY")
SQLALCHEMY_DATABASE_URI = env("SUPERSET_METADATA_URI")
SQLALCHEMY_EXAMPLES_URI = None

CACHE_CONFIG = _redis("superset_", 300)
DATA_CACHE_CONFIG = _redis("superset_data_", 300)
FILTER_STATE_CACHE_CONFIG = _redis("superset_filter_", 86_400)
EXPLORE_FORM_DATA_CACHE_CONFIG = _redis("superset_explore_", 86_400)

BABEL_DEFAULT_LOCALE = "fa"
LANGUAGES = {
    "fa": {"flag": "ir", "name": "فارسی"},
    "en": {"flag": "us", "name": "English"},
}

_FONT = "https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;700&display=swap"
THEME_DEFAULT = {
    **_THEME_DEFAULT,
    "token": {
        **_THEME_DEFAULT["token"],
        "fontUrls": [_FONT],
        "fontFamily": "Vazirmatn, Inter, sans-serif",
    },
}
THEME_DARK = None if _THEME_DARK is None else {
    **THEME_DEFAULT,
    "token": {
        **THEME_DEFAULT["token"],
        "colorEditorSelection": _THEME_DARK["token"].get("colorEditorSelection", "#5c4d1a"),
    },
    "algorithm": "dark",
}

FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DYNAMIC_PLUGINS": True,
}

JINJA_CONTEXT_ADDONS = dict(JINJA_ADDONS)
JALALI_SQL = {
    "dialect": "postgresql",
    "digits": "latin",
    "min_year": int(os.environ.get("JALALI_SQL_MIN_YEAR", "1390")),
    "max_year": int(os.environ.get("JALALI_SQL_MAX_YEAR", "1420")),
}

# DYNAMIC_PLUGINS without this blueprint makes every dashboard spin (F7/F8).
if env_bool("JALALI_BLUEPRINT_ENABLED", True):
    BLUEPRINTS = [jalali_datefilter_bp]
else:
    BLUEPRINTS = []

JALALI_DATEFILTER = {
    "enabled": env_bool("JALALI_DATEFILTER_ENABLED", True),
    "bundle": os.environ.get("JALALI_DATEFILTER_BUNDLE", "main"),
    "version": "1.0.0",
}

GUEST_ROLE_NAME = "EmbedGuest"
GUEST_TOKEN_JWT_SECRET = env("GUEST_TOKEN_JWT_SECRET")
GUEST_TOKEN_JWT_EXP_SECONDS = int(os.environ.get("GUEST_TOKEN_JWT_EXP_SECONDS", "300"))
# Fixed audience: token minting and validation must not depend on the request host.
GUEST_TOKEN_JWT_AUDIENCE = env("SUPERSET_PUBLIC_URL")

HOST_APP_ORIGINS = env_list("HOST_APP_ORIGINS", ["http://localhost:8101"])
ENABLE_CORS = True
CORS_OPTIONS = {
    **_CORS_OPTIONS,
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": list(dict.fromkeys([*_CORS_OPTIONS.get("origins", []), *HOST_APP_ORIGINS])),
}

TALISMAN_ENABLED = env_bool("TALISMAN_ENABLED", True)
_csp = dict(_TALISMAN_CONFIG["content_security_policy"])
_csp["frame-ancestors"] = ["'self'", *HOST_APP_ORIGINS]
TALISMAN_CONFIG = {
    **_TALISMAN_CONFIG,
    "content_security_policy": _csp,
    "frame_options": None,
}

SESSION_COOKIE_SAMESITE = os.environ.get("SUPERSET_SESSION_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SECURE = env_bool("SUPERSET_SESSION_COOKIE_SECURE", False)
SESSION_COOKIE_HTTPONLY = True

WEBDRIVER_BASEURL = env("SUPERSET_INTERNAL_URL")
PREFERRED_DATABASES = ["PostgreSQL"]
PREVENT_UNSAFE_DB_CONNECTIONS = True
SUPERSET_LOAD_EXAMPLES = False
