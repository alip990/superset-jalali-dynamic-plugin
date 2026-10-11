"""Persian names used by the Jalali column macros.

Letters are Persian yeh/keh (ی/ک), and ZWNJ is used where Persian orthography
requires it (سه‌شنبه).
"""

from __future__ import annotations

MONTHS: tuple[str, ...] = (
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
)

SEASONS: tuple[str, ...] = ("بهار", "تابستان", "پاییز", "زمستان")

# Saturday = 0, matching the date-filter grid.
WEEKDAYS: tuple[str, ...] = (
    "شنبه",
    "یکشنبه",
    "دوشنبه",
    "سه\u200cشنبه",
    "چهارشنبه",
    "پنجشنبه",
    "جمعه",
)
