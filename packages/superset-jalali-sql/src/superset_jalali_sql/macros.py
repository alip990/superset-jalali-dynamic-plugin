"""Jinja macros that expand a date column into Jalali display columns.

Filtering stays on the Gregorian column. These fragments are for labels and
grouping inside a virtual dataset. ``col``, ``alias`` and ``prefix`` are
validated and the macros return SQL text only.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from superset_jalali_sql.calendar import (
    MAX_YEAR,
    MIN_YEAR,
    NOWRUZ_DATES,
    g2j,
    j2g,
    parse_jalali,
)
from superset_jalali_sql.dialects import Dialect, get_dialect
from superset_jalali_sql.names import MONTHS, SEASONS, WEEKDAYS

DEFAULT_CONFIG: dict[str, Any] = {
    "dialect": "postgresql",
    "digits": "latin",
    "min_year": 1390,
    "max_year": 1420,
}

_PERIODS = ("this_month", "last_month", "this_year", "last_year", "ytd")
_TEXT_COLUMNS = {
    "date",
    "month",
    "month_name",
    "month_label",
    "season",
    "season_key",
    "weekday",
}


def sql_config() -> dict[str, Any]:
    """Read ``JALALI_SQL`` from the Flask app when one is active."""
    config = dict(DEFAULT_CONFIG)
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            override = current_app.config.get("JALALI_SQL") or {}
            config.update(override)
    except Exception:
        pass
    return config


def _dialect() -> Dialect:
    return get_dialect(str(sql_config()["dialect"]))


def _years() -> list[tuple[int, str, str]]:
    config = sql_config()
    min_year = int(config["min_year"])
    max_year = int(config["max_year"])
    if min_year < MIN_YEAR or max_year > MAX_YEAR or min_year > max_year:
        raise ValueError(
            f"JALALI_SQL year bounds {min_year}..{max_year} "
            f"must sit inside {MIN_YEAR}..{MAX_YEAR}"
        )
    return [
        (year, NOWRUZ_DATES[year].isoformat(), NOWRUZ_DATES[year + 1].isoformat())
        for year in range(min_year, max_year + 1)
    ]


def _digits(explicit: str | None) -> str:
    digits = explicit if explicit is not None else str(sql_config()["digits"])
    if digits not in ("latin", "persian"):
        raise ValueError(f"invalid digits mode: {digits!r}")
    return digits


def _null_if_unmatched(alias: str, expression: str, dialect: Dialect) -> str:
    quoted = dialect.quote_ident(alias)
    return f"(CASE WHEN {quoted}.jy IS NULL THEN NULL ELSE {expression} END)"


def _case_int(expression: str, labels: tuple[str, ...], dialect: Dialect) -> str:
    branches = " ".join(
        f"WHEN {index} THEN {dialect.sql_string(label)}"
        for index, label in enumerate(labels, start=1)
    )
    return f"(CASE {expression} {branches} ELSE NULL END)"


def jalali_join(col: str, alias: str = "_jy") -> str:
    """``LEFT JOIN`` a year-range table onto ``col`` (half-open Gregorian years)."""
    dialect = _dialect()
    quoted = dialect.quote_column(col)
    dialect.quote_ident(alias)
    return dialect.values_join(alias, quoted, _years())


def jalali_columns(
    col: str,
    alias: str = "_jy",
    prefix: str = "jalali_",
    digits: str | None = None,
) -> str:
    """Thirteen Jalali columns. Every column is NULL when no year matches."""
    dialect = _dialect()
    quoted = dialect.quote_column(col)
    quoted_alias = dialect.quote_ident(alias)
    digit_mode = _digits(digits)
    offset = dialect.day_offset(quoted, alias)
    month = dialect.month_num(offset)
    day = dialect.day_num(offset)
    year = f"{quoted_alias}.jy"
    weekday = dialect.weekday_sat0(quoted)
    season_num = f"(({month} - 1) / 3 + 1)"

    def name(suffix: str) -> str:
        full = f"{prefix}{suffix}"
        return dialect.quote_ident(full)

    def text(expression: str, suffix: str) -> str:
        if digit_mode == "persian" and suffix in _TEXT_COLUMNS:
            expression = dialect.translate_digits(expression)
        return _null_if_unmatched(alias, expression, dialect)

    lpad2 = "2, '0'"
    date_text = (
        f"(lpad({year}::text, 4, '0') || '/' || "
        f"lpad(({month})::text, {lpad2}) || '/' || "
        f"lpad(({day})::text, {lpad2}))"
    )
    month_text = f"(lpad({year}::text, 4, '0') || '-' || lpad(({month})::text, {lpad2}))"
    month_name = _case_int(month, MONTHS, dialect)
    season_name = _case_int(season_num, SEASONS, dialect)
    weekday_name = (
        f"(CASE {weekday} "
        + " ".join(
            f"WHEN {index} THEN {dialect.sql_string(label)}"
            for index, label in enumerate(WEEKDAYS)
        )
        + " ELSE NULL END)"
    )
    columns = {
        "year": (f"{year}", False),
        "month_num": (month, False),
        "day": (day, False),
        "date": (date_text, True),
        "date_int": (f"({year} * 10000 + ({month}) * 100 + ({day}))", False),
        "month": (month_text, True),
        "month_name": (month_name, True),
        "month_label": (f"({month_text} || ' ' || {month_name})", True),
        "season": (season_name, True),
        "season_key": (f"(lpad({year}::text, 4, '0') || '-' || ({season_num})::text || ' ' || {season_name})", True),
        "weekday": (weekday_name, True),
        "weekday_num": (weekday, False),
        "week_start": (dialect.week_start(quoted), False),
    }
    parts: list[str] = []
    for suffix, (expression, is_text) in columns.items():
        rendered = text(expression, suffix) if is_text else _null_if_unmatched(alias, expression, dialect)
        parts.append(f"{rendered} AS {name(suffix)}")
    return ",\n".join(parts)


def jalali_to_gregorian(text: str) -> str:
    """Expand a Jalali date literal to a Gregorian ``DATE 'YYYY-MM-DD'``."""
    jy, jm, jd = parse_jalali(text)
    return _dialect().date_literal(j2g(jy, jm, jd).isoformat())


def tehran_today() -> date:
    return datetime.now(ZoneInfo("Asia/Tehran")).date()


def period_bounds(period: str, today: date | None = None) -> tuple[date, date]:
    """Half-open Gregorian bounds ``[start, end)`` for a named Jalali period."""
    if period not in _PERIODS:
        known = ", ".join(_PERIODS)
        raise ValueError(f"unknown Jalali period {period!r} (known: {known})")
    current = today or tehran_today()
    jy, jm, jd = g2j(current)
    if period == "this_month":
        return j2g(jy, jm, 1), _next_month(jy, jm)
    if period == "last_month":
        prev_y, prev_m = (jy - 1, 12) if jm == 1 else (jy, jm - 1)
        return j2g(prev_y, prev_m, 1), j2g(jy, jm, 1)
    if period == "this_year":
        return NOWRUZ_DATES[jy], NOWRUZ_DATES[jy + 1]
    if period == "last_year":
        return NOWRUZ_DATES[jy - 1], NOWRUZ_DATES[jy]
    # Year to date, today included.
    return NOWRUZ_DATES[jy], current + timedelta(days=1)


def _next_month(jy: int, jm: int) -> date:
    if jm == 12:
        return NOWRUZ_DATES[jy + 1]
    return j2g(jy, jm + 1, 1)


def jalali_period_sql(col: str, period: str) -> str:
    """Predicate on ``col`` for a Jalali period, using today in Asia/Tehran."""
    dialect = _dialect()
    start, end = period_bounds(period)
    cast = dialect.cast_date(dialect.quote_column(col))
    return (
        f"{cast} >= {dialect.date_literal(start.isoformat())} "
        f"AND {cast} < {dialect.date_literal(end.isoformat())}"
    )
