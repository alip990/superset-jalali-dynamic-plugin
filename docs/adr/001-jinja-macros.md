# ADR 001: Jalali columns via Jinja, not database objects

The analytical database cannot gain tables, views, functions, or columns. Superset already renders virtual-dataset SQL with Jinja, including `JINJA_CONTEXT_ADDONS`, when it fetches columns and when a chart queries. The macros expand to a `VALUES` join and scalar expressions in PostgreSQL. A dialect class is the extension point for another engine. The year window is configuration, not a schema change.
