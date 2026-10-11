"""Host page and guest-token broker. No date logic lives here."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app.superset_client import SupersetClient, SupersetError
from app.users import USERS, rls_rules

STATIC = Path(__file__).resolve().parents[1] / "static"


def embed_info_path() -> Path:
    return Path(os.environ.get("EMBED_INFO_PATH", "/var/lib/jalali/embed.json"))

app = FastAPI(title="فروش")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["HOST_APP_SECRET"],
    session_cookie="host_app_session",
    same_site="lax",
    https_only=os.environ.get("HOST_APP_COOKIE_SECURE", "false").lower() == "true",
    max_age=60 * 60 * 8,
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")

_client = SupersetClient()
_uuid: str | None = None


class LoginBody(BaseModel):
    user: str


def dashboard_uuid() -> str:
    """The UUID is looked up by slug once, during bootstrap, and cached on disk."""
    global _uuid
    if _uuid:
        return _uuid
    info_path = embed_info_path()
    if not info_path.is_file():
        raise HTTPException(status_code=503, detail="شناسه داشبورد هنوز آماده نیست")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    if info.get("slug") != os.environ.get("DASHBOARD_SLUG", "sales-jalali"):
        raise HTTPException(status_code=500, detail="اسلاگ داشبورد با پیکربندی یکی نیست")
    _uuid = info["uuid"]
    return _uuid


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.get("/api/embed-config")
def embed_config() -> dict:
    return {
        "supersetDomain": os.environ["SUPERSET_PUBLIC_URL"].rstrip("/"),
        "dashboardUuid": dashboard_uuid(),
    }


@app.get("/api/session")
def session(request: Request) -> dict:
    user_id = request.session.get("user")
    if user_id not in USERS:
        return {"user": None}
    return {"user": user_id, "display_name": USERS[user_id]["display_name"]}


@app.post("/api/login")
def login(body: LoginBody, request: Request) -> dict:
    user = USERS.get(body.user)
    if user is None:
        raise HTTPException(status_code=400, detail="کاربر ناشناخته است")
    request.session["user"] = body.user
    return {"user": body.user, "display_name": user["display_name"]}


@app.get("/api/guest-token")
def guest_token(request: Request) -> dict:
    user_id = request.session.get("user")
    if user_id not in USERS:
        raise HTTPException(status_code=401, detail="ابتدا وارد شوید")
    user = USERS[user_id]
    try:
        token = _client.guest_token(
            dashboard_uuid=dashboard_uuid(),
            rls=rls_rules(user_id),
            username=f"embed_{user_id}",
            display_name=str(user["display_name"]),
        )
    except SupersetError as exc:
        raise HTTPException(status_code=502, detail="دریافت دسترسی داشبورد ناموفق بود") from exc
    return {"token": token}
