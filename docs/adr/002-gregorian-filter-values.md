# ADR 002: The date filter stores Gregorian Superset time ranges

Superset applies a dashboard time range by replacing each chart's `TEMPORAL_RANGE` filter. That filter is on a real date column, so the database can use `orders(created_at)`. The picker shows inclusive Jalali dates and emits a half-open Gregorian range. If the plugin is disabled, saved dashboards still describe a range Superset understands. Calendar presets are fixed dates because the time-range grammar has no Jalali month boundary; rolling presets are used when the default must move.
