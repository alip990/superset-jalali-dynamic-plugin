#!/usr/bin/env python3
"""API checks against a running stack. No browser required."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

import psycopg

PUBLIC = os.environ.get("SUPERSET_PUBLIC_URL", "http://localhost:8100").rstrip("/")
HOST = os.environ.get("HOST_APP_URL", "http://localhost:8101").rstrip("/")
DSN = os.environ["JALALI_TEST_DSN"]
ADMIN_USER = os.environ.get("SUPERSET_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ["SUPERSET_ADMIN_PASSWORD"]
SERVICE_USER = os.environ.get("GUEST_TOKEN_SERVICE_USERNAME", "guest_token_service")
SERVICE_PASSWORD = os.environ["GUEST_TOKEN_SERVICE_PASSWORD"]


def request(method: str, url: str, payload: dict | None = None, token: str | None = None, guest: str | None = None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if guest:
        headers["X-GuestToken"] = guest
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read().decode()
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def login(username: str, password: str) -> str:
    status, body = request(
        "POST",
        f"{PUBLIC}/api/v1/security/login",
        {"username": username, "password": password, "provider": "db", "refresh": True},
    )
    assert status == 200, body
    return body["access_token"]


def decode_jwt(token: str) -> dict:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def main() -> None:
    status, anon = request("GET", f"{PUBLIC}/dynamic-plugins/api/read")
    assert status == 200 and anon == {"result": []}, (status, anon)
    print("anonymous plugin list is empty")

    admin = login(ADMIN_USER, ADMIN_PASSWORD)
    status, listed = request("GET", f"{PUBLIC}/dynamic-plugins/api/read", token=admin)
    assert status == 200 and listed["result"], listed
    print("admin plugin list", listed["result"][0]["bundle_url"])

    status, health = request("GET", f"{PUBLIC}/jalali-datefilter/health")
    assert status == 200 and health["ok"] is True, health
    print("plugin health", health)

    q = urllib.parse.quote("'2024-09-22T00:00:00 : 2024-10-22T00:00:00'")
    status, time_range = request("GET", f"{PUBLIC}/api/v1/time_range/?q={q}", token=admin)
    assert status == 200, time_range
    print("absolute time range", time_range["result"][0]["since"], time_range["result"][0]["until"])

    rolling = urllib.parse.quote("'DATEADD(DATETIME(\"today\"), -6, day) : DATEADD(DATETIME(\"today\"), 1, day)'")
    status, rolling_body = request("GET", f"{PUBLIC}/api/v1/time_range/?q={rolling}", token=admin)
    assert status == 200, rolling_body
    print("rolling time range accepted")

    service = login(SERVICE_USER, SERVICE_PASSWORD)
    status, denied = request("GET", f"{PUBLIC}/api/v1/dashboard/", token=service)
    assert status in {401, 403}, denied
    print("service account cannot list dashboards", status)

    host = urllib.request.Request(f"{HOST}/api/login", data=json.dumps({"user": "sara"}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(host, timeout=20) as response:
        cookie = response.headers["Set-Cookie"]
    token_req = urllib.request.Request(f"{HOST}/api/guest-token", headers={"Cookie": cookie.split(";", 1)[0]})
    with urllib.request.urlopen(token_req, timeout=20) as response:
        guest = json.loads(response.read().decode())["token"]
    claims = decode_jwt(guest)
    rules = claims["rls_rules"]
    assert rules == [{"dataset": None, "clause": "region IN ('north')"}] or rules == [{"clause": "region IN ('north')"}], rules
    assert all("created_at" not in rule["clause"] for rule in rules)
    print("guest token rls", rules)

    status, guest_plugins = request("GET", f"{PUBLIC}/dynamic-plugins/api/read", guest=guest)
    assert status == 200 and guest_plugins["result"], guest_plugins
    print("guest plugin list", guest_plugins["result"][0]["key"])

    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("CREATE TABLE sales._smoke_should_fail (id int)")
                raise SystemExit("superset_ro was able to create a table")
            except psycopg.errors.InsufficientPrivilege:
                conn.rollback()
            cur.execute(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM sales.orders o
                JOIN sales.branches b ON b.id = o.branch_id
                JOIN sales.regions r ON r.code = b.region_code
                WHERE o.created_at >= TIMESTAMP '2024-09-22'
                  AND o.created_at < TIMESTAMP '2024-10-22'
                  AND r.code = 'north'
                """
            )
            expected = cur.fetchone()[0]
    print("north Mehr 1403 amount", expected)
    print("SMOKE_OK")


if __name__ == "__main__":
    main()
