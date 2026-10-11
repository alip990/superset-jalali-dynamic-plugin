"""Server-side Superset calls. The browser never sees the service-account password."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

TIMEOUT = 10


class SupersetError(RuntimeError):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"superset {status}: {detail}")
        self.status = status


class SupersetClient:
    def __init__(self) -> None:
        self.base = os.environ["SUPERSET_INTERNAL_URL"].rstrip("/")
        self._token: str | None = None
        self._csrf = ""
        self._cookie = ""

    def _login(self) -> str:
        payload = json.dumps(
            {
                "username": os.environ["GUEST_TOKEN_SERVICE_USERNAME"],
                "password": os.environ["GUEST_TOKEN_SERVICE_PASSWORD"],
                "provider": "db",
                "refresh": True,
            }
        ).encode()
        request = urllib.request.Request(
            f"{self.base}/api/v1/security/login",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            token = json.loads(response.read().decode())["access_token"]
        csrf_request = urllib.request.Request(
            f"{self.base}/api/v1/security/csrf_token/",
            headers={"Authorization": f"Bearer {token}", "Referer": self.base + "/"},
        )
        with urllib.request.urlopen(csrf_request, timeout=TIMEOUT) as response:
            self._csrf = json.loads(response.read().decode())["result"]
            self._cookie = response.headers.get("Set-Cookie", "").split(";", 1)[0]
        return token

    def _call(self, path: str, payload: dict, token: str) -> dict:
        request = urllib.request.Request(
            f"{self.base}{path}",
            data=json.dumps(payload).encode(),
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Referer": self.base + "/",
                "X-CSRFToken": self._csrf,
                "Cookie": self._cookie,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            raise SupersetError(exc.code, exc.read().decode()) from exc

    def guest_token(self, dashboard_uuid: str, rls: list[dict[str, str]], username: str, display_name: str) -> str:
        body = {
            "user": {"username": username, "first_name": display_name, "last_name": "مهمان"},
            "resources": [{"type": "dashboard", "id": dashboard_uuid}],
            "rls": rls,
        }
        if self._token is None:
            self._token = self._login()
        try:
            result = self._call("/api/v1/security/guest_token/", body, self._token)
        except SupersetError as exc:
            if exc.status != 401:
                raise
            self._token = self._login()
            result = self._call("/api/v1/security/guest_token/", body, self._token)
        return result["token"]
