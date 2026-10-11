"""Dialect lookup."""

from __future__ import annotations

from superset_jalali_sql.dialects.base import Dialect
from superset_jalali_sql.dialects.postgresql import PostgreSQLDialect

_DIALECTS: dict[str, Dialect] = {
    "postgresql": PostgreSQLDialect(),
}


def get_dialect(name: str) -> Dialect:
    try:
        return _DIALECTS[name]
    except KeyError as exc:
        known = ", ".join(sorted(_DIALECTS))
        raise ValueError(f"unsupported Jalali SQL dialect {name!r} (known: {known})") from exc


__all__ = ["Dialect", "get_dialect"]
