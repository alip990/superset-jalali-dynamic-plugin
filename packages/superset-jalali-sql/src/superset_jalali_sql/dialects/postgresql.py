"""PostgreSQL fragments for the Jalali macros."""

from __future__ import annotations

import re

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_COLUMN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?$")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


class PostgreSQLDialect:
    name = "postgresql"

    def quote_ident(self, name: str) -> str:
        if not _IDENT.match(name):
            raise ValueError(f"invalid identifier: {name!r}")
        return f'"{name}"'

    def quote_column(self, column: str) -> str:
        if not _COLUMN.match(column):
            raise ValueError(f"invalid column reference: {column!r}")
        return ".".join(self.quote_ident(part) for part in column.split("."))

    def date_literal(self, iso: str) -> str:
        if not _ISO.match(iso):
            raise ValueError(f"invalid date literal: {iso!r}")
        return f"DATE '{iso}'"

    def cast_date(self, quoted_column: str) -> str:
        return f"CAST({quoted_column} AS DATE)"

    def values_join(
        self,
        alias: str,
        quoted_column: str,
        rows: list[tuple[int, str, str]],
    ) -> str:
        quoted_alias = self.quote_ident(alias)
        values = ",\n".join(
            f"    ({int(year)}, {self.date_literal(start)}, {self.date_literal(end)})"
            for year, start, end in rows
        )
        cast = self.cast_date(quoted_column)
        return (
            f"LEFT JOIN (\nVALUES\n{values}\n) AS {quoted_alias}"
            f"(jy, start_date, next_start_date)\n"
            f"  ON {cast} >= {quoted_alias}.start_date\n"
            f" AND {cast} < {quoted_alias}.next_start_date"
        )

    def day_offset(self, quoted_column: str, alias: str) -> str:
        return (
            f"({self.cast_date(quoted_column)} - {self.quote_ident(alias)}.start_date)"
        )

    def month_num(self, offset: str) -> str:
        return (
            f"(CASE WHEN {offset} < 186 THEN ({offset} / 31) + 1 "
            f"ELSE (({offset} - 186) / 30) + 7 END)"
        )

    def day_num(self, offset: str) -> str:
        return (
            f"(CASE WHEN {offset} < 186 THEN ({offset} % 31) + 1 "
            f"ELSE (({offset} - 186) % 30) + 1 END)"
        )

    def weekday_sat0(self, quoted_column: str) -> str:
        # PostgreSQL DOW is Sunday = 0. Saturday-first numbering is (DOW + 1) % 7.
        return (
            f"((EXTRACT(DOW FROM {self.cast_date(quoted_column)})::int + 1) % 7)"
        )

    def week_start(self, quoted_column: str) -> str:
        return f"({self.cast_date(quoted_column)} - {self.weekday_sat0(quoted_column)})"

    def translate_digits(self, expression: str) -> str:
        return f"TRANSLATE({expression}, '0123456789', '{PERSIAN_DIGITS}')"

    def sql_string(self, value: str) -> str:
        return "'" + value.replace("'", "''") + "'"
