"""Every Gregorian day in the table, executed as superset_ro against Postgres."""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

psycopg = pytest.importorskip("psycopg")

from flask import Flask

from superset_jalali_sql.calendar import NOWRUZ_DATES, g2j
from superset_jalali_sql.macros import jalali_columns, jalali_join
from superset_jalali_sql.names import MONTHS, SEASONS, WEEKDAYS

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def connection():
    dsn = os.environ.get("JALALI_TEST_DSN")
    if not dsn:
        pytest.skip("JALALI_TEST_DSN is not set")
    with psycopg.connect(dsn) as conn:
        yield conn


def _sql(digits: str | None = None) -> str:
    columns = jalali_columns("d", digits=digits)
    join = jalali_join("d")
    start = NOWRUZ_DATES[1350].isoformat()
    end = (NOWRUZ_DATES[1552] - timedelta(days=1)).isoformat()
    return f"""
        SELECT d::date AS d, {columns}
        FROM generate_series('{start}'::date, '{end}'::date, interval '1 day') AS g(d)
        {join}
        ORDER BY 1
    """


def test_every_day_matches_python(connection) -> None:
    app = Flask(__name__)
    app.config["JALALI_SQL"] = {
        "dialect": "postgresql",
        "digits": "latin",
        "min_year": 1350,
        "max_year": 1551,
    }
    with app.app_context():
        statement = _sql()
    with connection.cursor() as cur:
        cur.execute(statement)
        rows = cur.fetchall()
    assert rows
    for (
        gregorian,
        year,
        month_num,
        day,
        jalali_date,
        date_int,
        month,
        month_name,
        month_label,
        season,
        season_key,
        weekday,
        weekday_num,
        week_start,
    ) in rows:
        jy, jm, jd = g2j(gregorian)
        assert (year, month_num, day) == (jy, jm, jd)
        assert jalali_date == f"{jy:04d}/{jm:02d}/{jd:02d}"
        assert date_int == jy * 10000 + jm * 100 + jd
        assert month == f"{jy:04d}-{jm:02d}"
        assert month_name == MONTHS[jm - 1]
        assert month_label == f"{jy:04d}-{jm:02d} {MONTHS[jm - 1]}"
        season_index = (jm - 1) // 3
        assert season == SEASONS[season_index]
        assert season_key == f"{jy}-{season_index + 1} {SEASONS[season_index]}"
        sat0 = (gregorian.weekday() + 2) % 7  # Python Monday=0; Saturday=0
        assert weekday_num == sat0
        assert weekday == WEEKDAYS[sat0]
        assert week_start == gregorian - timedelta(days=sat0)


def test_null_and_out_of_range_and_persian_digits(connection) -> None:
    app = Flask(__name__)
    app.config["JALALI_SQL"] = {
        "dialect": "postgresql",
        "digits": "persian",
        "min_year": 1403,
        "max_year": 1403,
    }
    with app.app_context():
        columns = jalali_columns("d", digits="persian")
        join = jalali_join("d")
    statement = f"""
        SELECT d::date, {columns}
        FROM (VALUES
            (DATE '2024-09-22'),
            (NULL::date),
            (DATE '1970-01-01')
        ) AS v(d)
        {join}
        ORDER BY d NULLS FIRST
    """
    with connection.cursor() as cur:
        cur.execute(statement)
        blank, null_row, mehr = cur.fetchall()
    assert null_row[1] is None and null_row[-1] is None
    assert blank[1] is None
    assert mehr[1] == 1403
    assert mehr[4] == "۱۴۰۳/۰۷/۰۱"


def test_superset_ro_cannot_create(connection) -> None:
    with connection.cursor() as cur:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("CREATE TABLE sales._jalali_should_fail (id int)")
    connection.rollback()
