#!/usr/bin/env python3
"""Provision Superset content. Safe to run more than once.

REST is used for the database, dataset, charts, dashboard and embedding.
Roles, permissions, metrics and the dashboard/chart link use the ORM, where
the API is awkward. The guest-token service account is not an admin.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import prison

DATASET_SQL = """
SELECT
    o.id,
    o.amount,
    o.quantity,
    o.status,
    o.created_at,
    CAST(o.created_at AS DATE) AS order_date,
    b.name_fa AS branch,
    r.code AS region,
    r.name_fa AS region_fa,
    p.category_fa AS category,
    {{ jalali_columns('o.created_at') }}
FROM sales.orders o
JOIN sales.branches b ON b.id = o.branch_id
JOIN sales.regions r ON r.code = b.region_code
JOIN sales.products p ON p.id = o.product_id
{{ jalali_join('o.created_at') }}
""".strip()

TEMPORAL = {
    "expressionType": "SIMPLE",
    "subject": "order_date",
    "operator": "TEMPORAL_RANGE",
    "comparator": "No filter",
    "clause": "WHERE",
}

# Views a guest must not keep even if Gamma has them.
_DENY_VIEWS = {
    "SQL Lab",
    "SQL Editor",
    "Saved Queries",
    "Query Search",
    "Queries",
    "Security",
    "List Users",
    "List Roles",
    "Row Level Security",
    "Row Level Security Filters",
    "Action Log",
    "Manage",
    "Import dashboards",
    "Alerts & Report",
    "Annotation Layers",
    "CSS Templates",
    "Data",
    "Datasets",
    "Databases",
    "Charts",
    "Dashboards",
}
_WRITE_PERMS = {"can_write", "can_edit", "can_add", "can_delete", "can_post", "can_put", "can_export", "can_mulexport"}
_WRITE_ALLOWED = {
    "DashboardFilterStateRestApi",
    "ExploreFormDataRestApi",
    "DashboardPermalinkRestApi",
    "ExplorePermalinkRestApi",
}
_REQUIRED = [
    ("can_read", "Dashboard"),
    ("can_list", "Dashboard"),
    ("can_show", "Dashboard"),
    ("can_read", "Chart"),
    ("can_list", "Chart"),
    ("can_show", "Chart"),
    ("can_read", "Dataset"),
    ("can_list", "Dataset"),
    ("can_show", "Dataset"),
    ("can_read", "Database"),
    ("can_read", "CurrentUserRestApi"),
    ("can_read", "EmbeddedDashboard"),
    ("can_list", "EmbeddedDashboard"),
    ("can_show", "EmbeddedDashboard"),
    ("can_dashboard", "Superset"),
    ("can_explore_json", "Superset"),
    ("can_log", "Superset"),
    ("can_slice", "Superset"),
    ("can_dashboard_permalink", "Superset"),
    ("can_time_range", "Api"),
    ("can_query", "Api"),
    ("can_query_form_data", "Api"),
    ("can_read", "DashboardFilterStateRestApi"),
    ("can_write", "DashboardFilterStateRestApi"),
    ("can_read", "ExploreFormDataRestApi"),
    ("can_write", "ExploreFormDataRestApi"),
    ("can_read", "DashboardPermalinkRestApi"),
    ("can_write", "DashboardPermalinkRestApi"),
    ("can_read", "ExplorePermalinkRestApi"),
    ("can_write", "ExplorePermalinkRestApi"),
    ("can_get", "Datasource"),
    ("can_external_metadata", "Datasource"),
    ("can_read", "CssTemplate"),
    ("can_read", "Theme"),
    ("can_read", "Annotation"),
]


class Api:
    def __init__(self, base: str, token: str) -> None:
        self.base = base.rstrip("/")
        self.token = token
        self.csrf = ""
        self.cookie = ""

    def request(self, method: str, path: str, payload: dict | None = None, params: dict | None = None):
        query = ""
        if params:
            query = "?" + "&".join(
                f"{key}={urllib.parse.quote(str(value))}" for key, value in params.items()
            )
        data = None if payload is None else json.dumps(payload).encode()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": self.base + "/",
            "X-CSRFToken": self.csrf,
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        req = urllib.request.Request(
            f"{self.base}{path}{query}",
            data=data,
            method=method,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                body = response.read().decode()
                return response.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()
            raise SystemExit(f"{method} {path} -> {exc.code} {detail}") from exc

    def find(self, path: str, column: str, value: str) -> dict | None:
        query = prison.dumps(
            {"filters": [{"col": column, "opr": "eq", "value": value}], "page_size": 1}
        )
        _status, body = self.request("GET", path, params={"q": query})
        rows = body.get("result") or []
        return rows[0] if rows else None


def login(base: str) -> Api:
    payload = json.dumps(
        {
            "username": os.environ["SUPERSET_ADMIN_USERNAME"],
            "password": os.environ["SUPERSET_ADMIN_PASSWORD"],
            "provider": "db",
            "refresh": True,
        }
    ).encode()
    root = base.rstrip("/")
    req = urllib.request.Request(
        f"{root}/api/v1/security/login",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        token = json.loads(response.read().decode())["access_token"]
    api = Api(root, token)
    csrf_req = urllib.request.Request(
        f"{root}/api/v1/security/csrf_token/",
        headers={"Authorization": f"Bearer {token}", "Referer": root + "/"},
    )
    with urllib.request.urlopen(csrf_req, timeout=30) as response:
        api.csrf = json.loads(response.read().decode())["result"]
        api.cookie = response.headers.get("Set-Cookie", "").split(";", 1)[0]
    return api


def wait_healthy(base: str) -> None:
    url = f"{base.rstrip('/')}/health"
    for _ in range(60):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(2)
    raise SystemExit("superset /health did not succeed")


def upsert_database(api: Api) -> int:
    found = api.find("/api/v1/database/", "database_name", "Analytics")
    payload = {
        "database_name": "Analytics",
        "sqlalchemy_uri": os.environ["ANALYTICS_SQLALCHEMY_URI"],
        "expose_in_sqllab": True,
        "allow_ctas": False,
        "allow_cvas": False,
        "allow_dml": False,
        "allow_run_async": False,
        "extra": json.dumps(
            {
                "allows_virtual_table_explore": True,
                "cancel_query_on_windows_unload": True,
            }
        ),
    }
    if found:
        api.request("PUT", f"/api/v1/database/{found['id']}", payload)
        return int(found["id"])
    _status, body = api.request("POST", "/api/v1/database/", payload)
    return int(body["id"])


def upsert_dataset(api: Api, database_id: int) -> int:
    found = api.find("/api/v1/dataset/", "table_name", "orders_jalali")
    if found:
        dataset_id = int(found["id"])
        api.request("PUT", f"/api/v1/dataset/{dataset_id}", {"sql": DATASET_SQL})
        return dataset_id
    _status, body = api.request(
        "POST",
        "/api/v1/dataset/",
        {
            "database": database_id,
            "table_name": "orders_jalali",
            "sql": DATASET_SQL,
            "normalize_columns": False,
        },
    )
    return int(body["id"])


def chart_params(dataset_id: int, viz: str, extra: dict) -> str:
    body = {
        "datasource": f"{dataset_id}__table",
        "viz_type": viz,
        "adhoc_filters": [TEMPORAL],
        "time_range": "No filter",
        "row_limit": extra.pop("row_limit", 10000),
        **extra,
    }
    return json.dumps(body)


def chart_specs(dataset_id: int) -> list[dict]:
    return [
        {
            "slice_name": "مجموع فروش",
            "viz_type": "big_number_total",
            "params": chart_params(dataset_id, "big_number_total", {"metric": "total_amount", "subheader": "مجموع فروش"}),
            "width": 4,
            "height": 30,
            "row": 0,
        },
        {
            "slice_name": "سهم دسته‌ها",
            "viz_type": "pie",
            "params": chart_params(dataset_id, "pie", {"groupby": ["category"], "metric": "total_amount", "row_limit": 100}),
            "width": 4,
            "height": 50,
            "row": 0,
        },
        {
            "slice_name": "فروش مناطق",
            "viz_type": "table",
            "params": chart_params(
                dataset_id,
                "table",
                {"query_mode": "aggregate", "groupby": ["region_fa"], "metrics": ["total_amount"], "row_limit": 100},
            ),
            "width": 4,
            "height": 50,
            "row": 0,
        },
        {
            "slice_name": "فروش ماهانه",
            "viz_type": "echarts_timeseries_bar",
            "params": chart_params(
                dataset_id,
                "echarts_timeseries_bar",
                {"x_axis": "jalali_month_label", "metrics": ["total_amount"], "groupby": [], "order_desc": False},
            ),
            "width": 12,
            "height": 50,
            "row": 1,
        },
        {
            "slice_name": "فروش روزانه",
            "viz_type": "echarts_timeseries_line",
            "params": chart_params(
                dataset_id,
                "echarts_timeseries_line",
                {"x_axis": "jalali_date", "metrics": ["total_amount"], "groupby": [], "order_desc": False},
            ),
            "width": 12,
            "height": 50,
            "row": 2,
        },
        {
            "slice_name": "فروش فصلی",
            "viz_type": "echarts_timeseries_bar",
            "params": chart_params(
                dataset_id,
                "echarts_timeseries_bar",
                {
                    "x_axis": "jalali_season_key",
                    "metrics": ["total_amount"],
                    "groupby": ["category"],
                    "stack": "Stack",
                    "order_desc": False,
                },
            ),
            "width": 6,
            "height": 50,
            "row": 3,
        },
        {
            "slice_name": "جدول محوری",
            "viz_type": "pivot_table_v2",
            "params": chart_params(
                dataset_id,
                "pivot_table_v2",
                {
                    "groupbyRows": ["jalali_year"],
                    "groupbyColumns": ["jalali_month_label"],
                    "metrics": ["total_amount"],
                    "aggregateFunction": "Sum",
                    "rowOrder": "key_a_to_z",
                    "colOrder": "key_a_to_z",
                    "valueFormat": ",.0f",
                },
            ),
            "width": 6,
            "height": 50,
            "row": 3,
        },
        {
            "slice_name": "آخرین سفارش‌ها",
            "viz_type": "table",
            "params": chart_params(
                dataset_id,
                "table",
                {
                    "query_mode": "raw",
                    "all_columns": ["jalali_date", "branch", "category", "amount"],
                    "order_by_cols": ['["jalali_date_int", false]'],
                    "row_limit": 100,
                },
            ),
            "width": 12,
            "height": 50,
            "row": 4,
        },
    ]


def upsert_charts(api: Api, dataset_id: int) -> list[dict]:
    created = []
    for spec in chart_specs(dataset_id):
        found = api.find("/api/v1/chart/", "slice_name", spec["slice_name"])
        payload = {
            "slice_name": spec["slice_name"],
            "viz_type": spec["viz_type"],
            "datasource_id": dataset_id,
            "datasource_type": "table",
            "params": spec["params"],
        }
        if found:
            api.request("PUT", f"/api/v1/chart/{found['id']}", payload)
            chart_id = int(found["id"])
        else:
            _status, body = api.request("POST", "/api/v1/chart/", payload)
            chart_id = int(body["id"])
        _status, full = api.request("GET", f"/api/v1/chart/{chart_id}")
        result = full["result"]
        created.append({**spec, "id": chart_id, "uuid": result.get("uuid")})
    return created


def position(charts: list[dict]) -> dict:
    rows: dict[int, list[dict]] = {}
    for chart in charts:
        rows.setdefault(chart["row"], []).append(chart)
    row_ids = [f"ROW-{index}" for index in sorted(rows)]
    layout: dict = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": row_ids, "parents": ["ROOT_ID"]},
    }
    for index in sorted(rows):
        row_id = f"ROW-{index}"
        children = []
        layout[row_id] = {
            "type": "ROW",
            "id": row_id,
            "children": children,
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        for offset, chart in enumerate(rows[index]):
            component = f"CHART-{chart['id']}-{offset}"
            children.append(component)
            layout[component] = {
                "type": "CHART",
                "id": component,
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {
                    "chartId": chart["id"],
                    "sliceName": chart["slice_name"],
                    "uuid": chart["uuid"],
                    "width": chart["width"],
                    "height": chart["height"],
                },
            }
    return layout


def native_filters(dataset_id: int, chart_ids: list[int]) -> list[dict]:
    scope = {"rootPath": ["ROOT_ID"], "excluded": []}
    empty_mask = {"extraFormData": {}, "filterState": {}, "ownState": {}}

    def base(filter_id: str, name: str, filter_type: str, targets: list[dict], parents: list[str] | None = None) -> dict:
        return {
            "id": filter_id,
            "name": name,
            "filterType": filter_type,
            "targets": targets,
            "defaultDataMask": empty_mask,
            "cascadeParentIds": parents or [],
            "scope": scope,
            "controlValues": {
                "enableEmptyFilter": False,
                "defaultToFirstItem": False,
                "multiSelect": True,
                "searchAllOptions": False,
                "inverseSelection": False,
            },
            "type": "NATIVE_FILTER",
            "description": "",
            "chartsInScope": chart_ids,
            "tabsInScope": [],
        }

    column = lambda name: [{"datasetId": dataset_id, "column": {"name": name}}]
    return [
        base("NATIVE_FILTER-date", "تاریخ", "filter_time", [{}]),
        base("NATIVE_FILTER-year", "سال", "filter_select", column("jalali_year")),
        base("NATIVE_FILTER-month", "ماه", "filter_select", column("jalali_month_label"), ["NATIVE_FILTER-year"]),
        base("NATIVE_FILTER-category", "دسته", "filter_select", column("category")),
    ]


def upsert_dashboard(api: Api, charts: list[dict], dataset_id: int) -> dict:
    metadata = {
        "native_filter_configuration": native_filters(dataset_id, [chart["id"] for chart in charts]),
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "color_scheme": "",
        "label_colors": {},
        "shared_label_colors": {},
        "cross_filters_enabled": False,
        "chart_configuration": {},
        "default_filters": "{}",
    }
    payload = {
        "dashboard_title": "داشبورد فروش",
        "slug": "sales-jalali",
        "published": True,
        "json_metadata": json.dumps(metadata, ensure_ascii=False),
        "position_json": json.dumps(position(charts), ensure_ascii=False),
    }
    try:
        _status, existing = api.request("GET", "/api/v1/dashboard/sales-jalali")
        dashboard_id = int(existing["result"]["id"])
        api.request("PUT", f"/api/v1/dashboard/{dashboard_id}", payload)
    except SystemExit:
        _status, created = api.request("POST", "/api/v1/dashboard/", payload)
        dashboard_id = int(created["id"])
    return {"id": dashboard_id}


def enable_embed(api: Api, dashboard_id: int) -> str:
    origins = [item.strip() for item in os.environ["HOST_APP_ORIGINS"].split(",") if item.strip()]
    _status, body = api.request(
        "POST",
        f"/api/v1/dashboard/{dashboard_id}/embedded",
        {"allowed_domains": origins},
    )
    return body["result"]["uuid"]


def configure_metadata(dataset_id: int, chart_ids: list[int], dashboard_id: int) -> None:
    from superset.app import create_app

    app = create_app()
    with app.app_context():
        from superset.connectors.sqla.models import SqlaTable, SqlMetric
        from superset.extensions import db
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice
        dataset = db.session.get(SqlaTable, dataset_id)
        dataset.main_dttm_col = "order_date"
        for column in dataset.columns:
            if column.column_name in {"order_date", "created_at"}:
                column.is_dttm = True
        by_name = {metric.metric_name: metric for metric in dataset.metrics}
        definitions = {
            "total_amount": ("SUM(amount)", "مجموع فروش"),
            "orders": ("COUNT(*)", "تعداد سفارش"),
        }
        for name, (expression, verbose) in definitions.items():
            metric = by_name.get(name)
            if metric is None:
                metric = SqlMetric(metric_name=name, expression=expression, table=dataset)
                db.session.add(metric)
            metric.expression = expression
            metric.verbose_name = verbose
        dashboard = db.session.get(Dashboard, dashboard_id)
        dashboard.slices = db.session.query(Slice).filter(Slice.id.in_(chart_ids)).all()
        dashboard.published = True
        _grant_roles(app, dataset)
        db.session.commit()


def _grant(sm, role, permission: str, view: str) -> None:
    permission_view = sm.find_permission_view_menu(permission, view)
    if permission_view is None:
        print(f"permission missing, skipped: {permission} on {view}", flush=True)
        return
    sm.add_permission_role(role, permission_view)


def _grant_roles(app, dataset) -> None:
    sm = app.appbuilder.sm
    gamma = sm.find_role("Gamma")
    guest = sm.find_role("EmbedGuest") or sm.add_role("EmbedGuest")
    if gamma is not None:
        guest.permissions = [
            item
            for item in gamma.permissions
            if item.view_menu.name not in _DENY_VIEWS
            and not (
                item.permission.name in _WRITE_PERMS
                and item.view_menu.name not in _WRITE_ALLOWED
            )
            and item.permission.name not in {"all_datasource_access", "all_database_access", "can_grant_guest_token"}
        ]
    for permission, view in _REQUIRED:
        _grant(sm, guest, permission, view)
    dataset_perm = dataset.get_perm()
    if sm.find_permission_view_menu("datasource_access", dataset_perm) is None:
        sm.add_permission_view_menu("datasource_access", dataset_perm)
    _grant(sm, guest, "datasource_access", dataset_perm)

    service = sm.find_role("GuestTokenService") or sm.add_role("GuestTokenService")
    service.permissions = []
    # grant_guest_token is the only security capability. can_read is required
    # to fetch the CSRF token that Flask-WTF demands on the guest-token POST.
    _grant(sm, service, "can_grant_guest_token", "SecurityRestApi")
    _grant(sm, service, "can_read", "SecurityRestApi")
    password = os.environ["GUEST_TOKEN_SERVICE_PASSWORD"]
    user = sm.find_user(username="guest_token_service")
    if user is None:
        sm.add_user(
            username="guest_token_service",
            first_name="Guest",
            last_name="Token",
            email="guest-token@localhost",
            role=service,
            password=password,
        )
    else:
        user.roles = [service]
        user.password = password
    kept = sorted(f"{item.permission.name} on {item.view_menu.name}" for item in guest.permissions)
    print("EMBED_GUEST_PERMISSIONS", len(kept), flush=True)
    for line in kept:
        print(f"  {line}", flush=True)


def main() -> None:
    base = os.environ["SUPERSET_INTERNAL_URL"]
    wait_healthy(base)
    api = login(base)
    database_id = upsert_database(api)
    dataset_id = upsert_dataset(api, database_id)
    charts = upsert_charts(api, dataset_id)
    dashboard = upsert_dashboard(api, charts, dataset_id)
    configure_metadata(dataset_id, [chart["id"] for chart in charts], dashboard["id"])
    # Filters were written before chart ids were linked; write them again now that
    # chartsInScope is known and the dataset columns exist.
    api.request(
        "PUT",
        f"/api/v1/dashboard/{dashboard['id']}",
        {
            "json_metadata": json.dumps(
                {
                    "native_filter_configuration": native_filters(dataset_id, [chart["id"] for chart in charts]),
                    "cross_filters_enabled": False,
                    "refresh_frequency": 0,
                    "default_filters": "{}",
                },
                ensure_ascii=False,
            )
        },
    )
    embedded = enable_embed(api, dashboard["id"])
    out = Path(os.environ.get("EMBED_INFO_PATH", "/var/lib/jalali/embed.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "slug": "sales-jalali",
                "uuid": embedded,
                "dashboard_id": dashboard["id"],
                "dataset_id": dataset_id,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out.chmod(0o644)
    print(
        "BOOTSTRAP_DONE",
        json.dumps({"dashboard_id": dashboard["id"], "dataset_id": dataset_id, "embedded_uuid": embedded}),
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("BOOTSTRAP_FAILED", file=sys.stderr)
        raise
