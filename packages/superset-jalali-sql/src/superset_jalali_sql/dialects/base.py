"""Dialect interface for Jalali SQL fragments.

Only PostgreSQL is implemented. Another engine needs a small subclass that
emits the same column meanings.
"""

from __future__ import annotations

from typing import Protocol


class Dialect(Protocol):
    name: str

    def quote_ident(self, name: str) -> str: ...

    def quote_column(self, column: str) -> str: ...

    def date_literal(self, iso: str) -> str: ...

    def cast_date(self, quoted_column: str) -> str: ...

    def values_join(
        self,
        alias: str,
        quoted_column: str,
        rows: list[tuple[int, str, str]],
    ) -> str: ...

    def day_offset(self, quoted_column: str, alias: str) -> str: ...

    def month_num(self, offset: str) -> str: ...

    def day_num(self, offset: str) -> str: ...

    def weekday_sat0(self, quoted_column: str) -> str: ...

    def week_start(self, quoted_column: str) -> str: ...

    def translate_digits(self, expression: str) -> str: ...

    def sql_string(self, value: str) -> str: ...
