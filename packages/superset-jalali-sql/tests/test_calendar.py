"""Calendar conversion against the generated Nowruz table and jdatetime."""

from __future__ import annotations

from datetime import date, timedelta

import jdatetime
import pytest

from superset_jalali_sql.calendar import (
    MAX_YEAR,
    MIN_YEAR,
    NOWRUZ_DATES,
    g2j,
    j2g,
    month_length,
    parse_jalali,
)


def test_anchors() -> None:
    assert j2g(1403, 1, 1) == date(2024, 3, 20)
    assert j2g(1404, 1, 1) == date(2025, 3, 21)
    assert j2g(1405, 1, 1) == date(2026, 3, 21)
    assert j2g(1403, 12, 30) == date(2025, 3, 20)
    assert j2g(1403, 7, 1) == date(2024, 9, 22)
    assert j2g(1403, 7, 30) == date(2024, 10, 21)
    assert j2g(1403, 8, 1) == date(2024, 10, 22)


def test_leap_and_non_leap_esfand() -> None:
    assert month_length(1403, 12) == 30
    assert month_length(1404, 12) == 29
    assert month_length(1403, 1) == 31
    assert month_length(1403, 7) == 30
    with pytest.raises(ValueError):
        j2g(1404, 12, 30)
    with pytest.raises(ValueError):
        month_length(1403, 13)


def test_round_trip_and_jdatetime_every_day() -> None:
    current = NOWRUZ_DATES[MIN_YEAR]
    end = NOWRUZ_DATES[MAX_YEAR + 1]
    while current < end:
        converted = g2j(current)
        library = jdatetime.date.fromgregorian(date=current)
        assert converted == (library.year, library.month, library.day)
        assert j2g(*converted) == current
        current += timedelta(days=1)


def test_out_of_range() -> None:
    with pytest.raises(ValueError):
        g2j(NOWRUZ_DATES[MIN_YEAR] - timedelta(days=1))
    with pytest.raises(ValueError):
        g2j(NOWRUZ_DATES[MAX_YEAR + 1])
    with pytest.raises(ValueError):
        j2g(MIN_YEAR - 1, 1, 1)
    with pytest.raises(ValueError):
        j2g(MAX_YEAR + 1, 1, 1)


def test_parse_digits_and_separators() -> None:
    assert parse_jalali("1403/07/18") == (1403, 7, 18)
    assert parse_jalali("1403-07-18") == (1403, 7, 18)
    assert parse_jalali("۱۴۰۳/۰۷/۱۸") == (1403, 7, 18)
    assert parse_jalali("١٤٠٣/٠٧/١٨") == (1403, 7, 18)
    with pytest.raises(ValueError):
        parse_jalali("1403/13/01")
    with pytest.raises(ValueError):
        parse_jalali("not a date")
    with pytest.raises(ValueError):
        parse_jalali("1404/12/30")
