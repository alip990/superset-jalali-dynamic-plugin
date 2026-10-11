# Operations

## Deploy

1. Set every secret in the environment. Start from `.env.example`. Do not commit `.env`.
2. Point `SUPERSET_PUBLIC_URL` at the browser-facing origin and `SUPERSET_INTERNAL_URL` at the URL the host app uses inside the network.
3. Set `HOST_APP_ORIGINS` to the exact origins that may iframe Superset. Talisman `frame-ancestors`, CORS, and the dashboard's embedded domains all use this list.
4. Over HTTPS, set `SUPERSET_SESSION_COOKIE_SAMESITE=None` and `SUPERSET_SESSION_COOKIE_SECURE=true`. Local HTTP must stay `Lax` and `false`; browsers drop `SameSite=None` cookies that are not Secure.
5. `make up`, then confirm `BOOTSTRAP_DONE` in the bootstrap logs and `ok: true` from `/jalali-datefilter/health` and the host `/healthz`.

`JALALI_SQL_MIN_YEAR` and `JALALI_SQL_MAX_YEAR` should cover the data and not the whole 1350–1551 table. Filtering stays on `created_at` / `order_date`, which are indexed.

## Upgrade Superset

On a staging copy, change the `apache/superset` tag and rebuild. Re-run the Milestone 0 checks that can break without a code change:

- plugin list returns 200 for an admin and an empty list for an anonymous caller
- the time filter is replaced in an admin session and inside the iframe
- the shared-module shape still matches the shims (`window['__superset__/react']` and `@superset-ui/core`)
- a missing bundle still lets the dashboard load with the stock picker
- the Playwright flow for Mehr 1403

Then promote the same tag. We depend on `filter.dateFilterControl`, `DateFilterControlProps`, the dynamic plugin loader, its shared modules, and React 17. When Superset ships a supported date-filter extension point, port the control onto it.

## Kill switch

`JALALI_DATEFILTER_ENABLED=false` serves an empty plugin list. The next page load uses the stock picker. Saved values are ordinary Superset time ranges, so they remain valid.

Never set `DYNAMIC_PLUGINS` without the blueprint (`JALALI_BLUEPRINT_ENABLED` must stay true). A missing or failing list endpoint leaves every dashboard on the loading spinner.

`JALALI_DATEFILTER_BUNDLE=hello` serves the red probe button instead of the calendar. Use it only to re-check the loader.

## Health

| Check | Where |
|---|---|
| Superset process | `GET /health` |
| Plugin | `GET /jalali-datefilter/health` and `window.__JALALI_DATEFILTER__` in the browser |
| Host app | `GET /healthz` |

## Security

- Guest-token RLS is for security attributes only.
- `guest_token_service` has `can_grant_guest_token` on `SecurityRestApi` and no content permissions. The dashboard UUID is written by bootstrap and read by the host app, so the service account does not need to list dashboards.
- Talisman stays on. `frame-ancestors` is `'self'` plus `HOST_APP_ORIGINS`. `X-Frame-Options` is disabled because `frame-ancestors` replaces it.
- The bundle is built in CI from this source and served from the Superset origin.
- Template processing is on for dataset authors. Treat those accounts as trusted.
- `superset_ro` has `CONNECT`, `USAGE` on `sales`, and `SELECT`. It cannot create objects.

## Performance

Keep the Jalali year window tight. Filter on Gregorian columns. Redis caches query, data, filter state, and explore form data. Watch per-row Jalali expressions on very large tables; the join is one row per year in the window, not per day.

## Troubleshooting

| What you see | What to check |
|---|---|
| Dashboard spins forever | `DYNAMIC_PLUGINS` is on and `/dynamic-plugins/api/read` is not 200. The blueprint is missing or threw. It is written to return 200 even on failure; a spinner means the route is absent or a proxy is eating it. |
| Stock Gregorian picker | Bundle failed. Console for `jalali-datefilter:`, then `/jalali-datefilter/health`. `enabled: false` also does this, on purpose. |
| Date filter does not change charts | The chart has no `No filter` time pill on a temporal column, or the dataset has no main datetime column. |
| Iframe refused | CORS origin, `frame-ancestors`, or the dashboard's allowed domains. All three must include the host origin. |
| Guest 401 or 403 | `EmbedGuest` is missing a permission the screen calls, or `GUEST_TOKEN_JWT_SECRET` / audience does not match. Audience is `SUPERSET_PUBLIC_URL`. |
| Jalali columns NULL | The date is outside `JALALI_SQL` min/max year, or the column is NULL. |
| Charts show Gregorian axis labels | The chart is on a real time axis. Use a Jalali category column. |
