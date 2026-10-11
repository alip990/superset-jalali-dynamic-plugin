"""Jalali calendar and Jinja SQL macros for Superset virtual datasets."""

from superset_jalali_sql.calendar import g2j, j2g, month_length, parse_jalali
from superset_jalali_sql.macros import (
    jalali_columns,
    jalali_join,
    jalali_period_sql,
    jalali_to_gregorian,
)

JINJA_ADDONS = {
    "jalali_columns": jalali_columns,
    "jalali_join": jalali_join,
    "jalali_to_gregorian": jalali_to_gregorian,
    "jalali_period_sql": jalali_period_sql,
}

__all__ = [
    "JINJA_ADDONS",
    "g2j",
    "j2g",
    "jalali_columns",
    "jalali_join",
    "jalali_period_sql",
    "jalali_to_gregorian",
    "month_length",
    "parse_jalali",
]
