"""Gregorian ↔ Jalali conversion driven only by the Nowruz table."""

from __future__ import annotations

import re
from datetime import date, timedelta

from superset_jalali_sql.nowruz import NOWRUZ

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_DATE_RE = re.compile(r"^(\d{4})[-/](\d{2})[-/](\d{2})$")

NOWRUZ_DATES: dict[int, date] = {
    year: date.fromisoformat(iso) for year, iso in NOWRUZ.items()
}
_YEARS: list[int] = sorted(NOWRUZ_DATES)
MIN_YEAR: int = _YEARS[0]
SENTINEL_YEAR: int = _YEARS[-1]
MAX_YEAR: int = SENTINEL_YEAR - 1


def month_length(jy: int, jm: int) -> int:
    """Days in a Jalali month. Esfand is 29, or 30 in a leap year."""
    if jy < MIN_YEAR or jy > MAX_YEAR:
        raise ValueError(f"Jalali year {jy} is outside {MIN_YEAR}..{MAX_YEAR}")
    if jm < 1 or jm > 12:
        raise ValueError(f"invalid Jalali month {jm}")
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return (NOWRUZ_DATES[jy + 1] - NOWRUZ_DATES[jy]).days - 336


def g2j(value: date) -> tuple[int, int, int]:
    """Convert a Gregorian date to ``(jalali_year, month, day)``."""
    if value < NOWRUZ_DATES[MIN_YEAR] or value >= NOWRUZ_DATES[SENTINEL_YEAR]:
        raise ValueError(f"{value.isoformat()} is outside the Jalali table")
    lo = 0
    hi = len(_YEARS) - 2
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if NOWRUZ_DATES[_YEARS[mid]] <= value:
            lo = mid
        else:
            hi = mid - 1
    jy = _YEARS[lo]
    doy = (value - NOWRUZ_DATES[jy]).days
    if doy < 186:
        return jy, doy // 31 + 1, doy % 31 + 1
    return jy, (doy - 186) // 30 + 7, (doy - 186) % 30 + 1


def j2g(jy: int, jm: int, jd: int) -> date:
    """Convert a Jalali date to a Gregorian ``date``. Invalid dates raise."""
    length = month_length(jy, jm)
    if jd < 1 or jd > length:
        raise ValueError(f"invalid Jalali date {jy:04d}/{jm:02d}/{jd:02d}")
    if jm <= 6:
        doy = (jm - 1) * 31 + (jd - 1)
    else:
        doy = 186 + (jm - 7) * 30 + (jd - 1)
    return NOWRUZ_DATES[jy] + timedelta(days=doy)


def parse_jalali(text: str) -> tuple[int, int, int]:
    """Parse ``YYYY/MM/DD`` or ``YYYY-MM-DD`` with Latin, Persian, or Arabic digits."""
    normalized = str(text).strip().translate(_DIGITS)
    match = _DATE_RE.match(normalized)
    if not match:
        raise ValueError(f"invalid Jalali date string: {text!r}")
    jy, jm, jd = (int(part) for part in match.groups())
    j2g(jy, jm, jd)
    return jy, jm, jd
