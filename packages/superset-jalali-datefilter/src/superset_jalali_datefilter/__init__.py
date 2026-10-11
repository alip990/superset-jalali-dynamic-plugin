"""Dashboard Jalali date filter: a blueprint plus a dynamic-plugin bundle."""

from superset_jalali_datefilter.blueprint import PLUGIN_KEY, blueprint

__all__ = ["PLUGIN_KEY", "blueprint"]
__version__ = "1.0.0"
