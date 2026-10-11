"""SQL macro shape, validation, and config."""

from __future__ import annotations

from datetime import date

import pytest
import sqlglot
from flask import Flask

from superset_jalali_sql.macros import (
    jalali_columns,
    jalali_join,
    jalali_period_sql,
    jalali_to_gregorian,
    period_bounds,
)
from superset_jalali_sql.names import MONTHS, WEEKDAYS


def _query(columns: str, join: str) -> str:
    return f"SELECT {columns}\nFROM sales.orders AS t\n{join}"


def test_default_year_window_is_narrow() -> None:
    sql = jalali_join("t.created_at")
    assert sql.count("DATE '") == 31 * 2
    assert "1390" in sql and "1420" in sql
    assert "1350" not in sql


def test_sqlglot_parses_postgresql() -> None:
    sql = _query(
        jalali_columns("t.created_at"),
        jalali_join("t.created_at"),
    )
    parsed = sqlglot.parse_one(sql, read="postgres")
    assert parsed is not None


def test_identifier_validation() -> None:
    with pytest.raises(ValueError):
        jalali_columns("t.created_at; DROP TABLE sales.orders")
    with pytest.raises(ValueError):
        jalali_join("created_at", alias="jy;--")
    with pytest.raises(ValueError):
        jalali_columns("t.created_at", prefix="jalali ")


def test_null_guard_and_persian_digits() -> None:
    latin = jalali_columns("o.created_at")
    assert latin.count("IS NULL THEN NULL") == 13
    assert "TRANSLATE" not in latin
    persian = jalali_columns("o.created_at", digits="persian")
    assert "TRANSLATE" in persian
    assert "۰۱۲۳۴۵۶۷۸۹" in persian
    for month in MONTHS:
        assert month in latin
    assert WEEKDAYS[3] == "سه\u200cشنبه"
    assert WEEKDAYS[3] in latin
    assert "CASE WHEN 0 THEN" not in latin


def test_distinct_alias_and_prefix() -> None:
    sql = jalali_columns("o.updated_at", alias="_upd", prefix="updated_")
    assert '"updated_year"' in sql
    assert '"_upd".jy' in sql
    assert "jalali_year" not in sql


def test_config_from_flask() -> None:
    app = Flask(__name__)
    app.config["JALALI_SQL"] = {
        "dialect": "postgresql",
        "digits": "latin",
        "min_year": 1403,
        "max_year": 1404,
    }
    with app.app_context():
        sql = jalali_join("t.created_at")
    assert "1403" in sql and "1404" in sql
    assert "1402" not in sql and "1405" not in sql.split("1404", 1)[-1]


def test_gregorian_literal_and_period() -> None:
    assert jalali_to_gregorian("1403/07/01") == "DATE '2024-09-22'"
    assert jalali_to_gregorian("۱۴۰۳/۰۷/۰۱") == "DATE '2024-09-22'"
    assert period_bounds("this_month", date(2024, 9, 22)) == (
        date(2024, 9, 22),
        date(2024, 10, 22),
    )
    assert period_bounds("last_month", date(2024, 9, 22)) == (
        date(2024, 8, 22),
        date(2024, 9, 22),
    )
    assert period_bounds("this_year", date(2024, 9, 22)) == (
        date(2024, 3, 20),
        date(2025, 3, 21),
    )
    assert period_bounds("ytd", date(2024, 9, 22)) == (
        date(2024, 3, 20),
        date(2024, 9, 23),
    )
    predicate = jalali_period_sql("o.created_at", "this_year")
    assert "CAST(" in predicate and "DATE '" in predicate
    with pytest.raises(ValueError):
        period_bounds("not-a-period")


def test_unknown_dialect() -> None:
    app = Flask(__name__)
    app.config["JALALI_SQL"] = {
        "dialect": "mysql",
        "digits": "latin",
        "min_year": 1403,
        "max_year": 1403,
    }
    with app.app_context():
        with pytest.raises(ValueError, match="dialect"):
            jalali_join("t.created_at")
