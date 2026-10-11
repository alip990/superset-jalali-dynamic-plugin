# Architecture

```
Browser
  host app (RTL) --iframe--> Superset 6.1.0
  host app API --guest token--> /api/v1/security/guest_token/
Superset
  dynamic plugin loader --> GET /dynamic-plugins/api/read (our blueprint)
  bundle registers filter.dateFilterControl
  Jinja macros from superset-jalali-sql
  SELECT only, role superset_ro
Analytics Postgres
  schema sales, untouched by Superset
```

Superset's image is `apache/superset:6.1.0` plus two pip packages. One package carries the JS bundle built in an earlier stage. Superset's frontend is not rebuilt and its source is not patched.

## Display

A virtual dataset calls the macros as a pair:

```sql
SELECT t.*, {{ jalali_columns('t.created_at') }}
FROM sales.orders t
{{ jalali_join('t.created_at') }}
```

`jalali_join` left-joins a `VALUES` list of Jalali years. `jalali_columns` emits 13 columns, all NULL when the date matches no year. Narrow `JALALI_SQL.min_year` / `max_year` to the data. A wide year list makes the join slower and does not change results inside the window.

The calendar math comes from `nowruz.py`. Python, the SQL expressions, and the date picker all use that table.

## Filtering

The dashboard Time range filter renders `getExtensionsRegistry().get('filter.dateFilterControl')`, falling back to Superset's picker. Our bundle registers the Jalali control at import time, before the filter bar paints, so there is no Gregorian flash when the bundle loads.

The control emits half-open Gregorian ranges (`start T00:00:00 : day-after-end T00:00:00`) or a rolling Superset expression such as `today : DATEADD(DATETIME("today"), 1, day)`. Charts must carry a `TEMPORAL_RANGE` filter on the Gregorian column with comparator `No filter`. The dashboard time range replaces that comparator. Jalali columns are not the filter target.

Calendar presets (this month, this year, …) are stored as fixed dates because Superset's time grammar cannot say "start of the Jalali month". Rolling presets move with the server clock. The containers run with `TZ=Asia/Tehran`.

## Embedding and RLS

The host app logs into Superset as `guest_token_service`, then calls `POST /api/v1/security/guest_token/`. The token's `rls` clause is built only from a whitelist of region codes, for example `region IN ('north')`. It has no dataset id, so Superset applies it to the outer query of every dataset. Every embedded dataset therefore needs a `region` column. Switching users unmounts the iframe and embeds again; the embedded SDK has no "set filter" message.

`GUEST_TOKEN_JWT_AUDIENCE` is `SUPERSET_PUBLIC_URL`, so minting the token from inside the Docker network and validating it from the browser use the same audience.

## The blueprint

`DYNAMIC_PLUGINS` makes the frontend call `GET /dynamic-plugins/api/read`. Flask-AppBuilder 5 removed that route. If the call fails, `loading` never clears. The blueprint serves the route, returns `{"result": []}` for anonymous users and on any error, and skips itself if a future Superset already registered the path. Static bundles are same-origin, content-hashed, and cached as immutable.
