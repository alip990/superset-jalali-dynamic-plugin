# Verified facts

Superset 6.1.0, commit `c83fb2b`, Flask-AppBuilder 5.0.2.

"Source" was read in the tagged tree or in the `apache/superset:6.1.0` image. "M0" is a check on this stack and is filled in after the run.

| # | Fact | Status | Evidence |
|---|---|---|---|
| F1 | Virtual dataset SQL is rendered with Jinja, including `JINJA_CONTEXT_ADDONS`, when columns are fetched and when charts query | Source | `superset/connectors/sqla/utils.py` `get_virtual_table_metadata()`; `superset/jinja_context.py` |
| F2 | Guest-token RLS rules without `dataset` apply to the outer query of every dataset | Source | `superset/connectors/sqla/models.py` `get_sqla_row_level_filters()` |
| F3 | The dashboard Time range filter renders `getExtensionsRegistry().get('filter.dateFilterControl') ?? DateFilterControl` with props `value`, `name`, `onChange`, `onOpenPopover`, `onClosePopover`, `isOverflowingFilterBar` | Source | `superset-frontend/src/filters/components/Time/TimeFilterPlugin.tsx` |
| F4 | Dynamic plugins receive the host's `react`, `react-dom`, `lodash`, `@superset-ui/core`, `@superset-ui/chart-controls` at `window["__superset__/<name>"]` before the bundle loads. `getExtensionsRegistry` is the singleton from `@superset-ui/core` | Source | `DynamicPlugins/index.tsx`; `dynamic-plugins/shared-modules.ts` |
| F5 | The dashboard shows a loading state until every dynamic plugin's `import()` settles, so a successful bundle does not flash the Gregorian picker | Source | `Dashboard.tsx`; `DashboardPage.tsx` |
| F6 | The embedded page includes the dynamic plugin loader. A guest token authenticates requests through `request_loader`. `GuestUser.is_authenticated` is true | Source | `EmbeddedContextProviders.tsx`; `security/manager.py`; `security/guest_token.py` |
| F7 | `GET /dynamic-plugins/api/read` was removed with Flask-AppBuilder 5. Upstream issue 35870 is closed as won't-fix | Source | `DynamicPlugins/index.tsx`; FAB 5.0.2 has no `RestCRUDView` route |
| F8 | If that call fails, `loading` stays true and dashboards spin | Source + live 404 | With `JALALI_BLUEPRINT_ENABLED=false`, `GET /dynamic-plugins/api/read` returned the Superset HTML 404. `fetchAll()` only logs that error and never clears `loading` |
| F9 | Blueprints in `BLUEPRINTS` are registered at startup | Source | `superset/initialization/__init__.py` `register_blueprints()` |
| F10 | A chart's `TEMPORAL_RANGE` adhoc filter receives the dashboard `time_range`. Charts need a "No filter" pill on the date column | Source | `query_context_factory.py` `_apply_filters()` |
| F11 | The 6.1.0 frontend uses React 17.0.2 | Source | `superset-frontend/package.json` |
| F12 | The embedded iframe accepts a new guest token and has no "set filter" message | Source | `superset-frontend/src/embedded/index.tsx` |
| F13 | The embedded SDK release matching 6.1.0 is 0.3.0 | Source | `superset-embedded-sdk/package.json` |
| F14 | `FEATURE_FLAGS` in `superset_config.py` replaces only the keys it sets; defaults live in `DEFAULT_FEATURE_FLAGS` and are merged at runtime | Source | `superset/utils/feature_flag_manager.py` |
| F15 | Assigning `THEME_DEFAULT` replaces the whole dict. Partial font overrides have to be merged in the config module. `THEME_DARK` is built from the original theme before the override, so it is rebuilt too | Source | end of `superset/config.py` (`from superset_config import *`) |
| F16 | Talisman is constructed with `talisman.init_app(app, **TALISMAN_CONFIG)`. `frame_options: None` drops `X-Frame-Options`. `frame-ancestors` is not in the 6.1 default policy; this config adds it | Source | `initialization/__init__.py`; `config.py` `TALISMAN_CONFIG` |
| F17 | Guest-token `aud` is `GUEST_TOKEN_JWT_AUDIENCE` when set, otherwise `WEBDRIVER_BASEURL`. It is not the request host. This stack sets the audience to `SUPERSET_PUBLIC_URL` so minting and validation match | Source | `security/manager.py` `_get_guest_token_jwt_audience`; `utils/urls.py` `get_url_host` |
| F18 | The embedded page calls `GET /api/v1/me/roles/` before it renders. That needs `can_read` on `CurrentUserRestApi`. Chart data uses `can_list` on `Chart` because `data` is mapped to `list` | Source | `embedded/index.tsx`; `charts/data/api.py`; FAB `protect` |
| M0-1 | Blueprint and bundle load as admin and as guest inside the iframe | Passed | Admin dashboard showed `HELLO No filter`. Guest `X-GuestToken` list returned the bundle; the iframe showed `HELLO No filter` and charts |
| M0-2 | `window["__superset__/react"]` is a module namespace with both named exports and `.default` (an object). `@superset-ui/core` has no `.default`; `getExtensionsRegistry` is on the namespace | Passed | Read in the embedded iframe main world. Shims use `default ?? namespace` |
| M0-3 | `2024-09-22T00:00:00 : 2024-10-22T00:00:00` is accepted. At 01:20 Asia/Tehran on 2026-10-11, `today` resolved to `2026-10-11`, not UTC `2026-10-10`. `DATEADD(..., -6, day)` resolved to `2026-10-05` | Passed | `GET /api/v1/time_range/?q='<string>'` (rison string, not an object) |
| M0-4 | Talisman CSP includes `frame-ancestors 'self' http://localhost:8101`. The hello bundle loaded in the iframe with no CSP block. Guest RLS `region IN ('north')` left only شمال, and Mehr 1403 changed the total from 9.57B to 371M | Passed | Response header on `/embedded/<uuid>`; SQL sum for north Mehr was 370,918,285 |
| M0-5 | Native filters use `id`, `filterType`, `targets`, `defaultDataMask`, `cascadeParentIds`, `scope.rootPath`, `chartsInScope`, `type: NATIVE_FILTER`. Pivot params use `groupbyRows` and `groupbyColumns` | Passed on the running API | Dashboard `json_metadata` written by bootstrap and rendered. `can_list` / `can_show` are not created by `superset init`; the views expose `can_read` |
| M0-6 | `EmbedGuest` was copied from Gamma, then SQL Lab menus and write permissions were removed, then `datasource_access` on `orders_jalali` was added (80 permissions). That set embedded successfully. `guest_token_service` needs `can_grant_guest_token` and `can_read` on `SecurityRestApi` (the CSRF token). It cannot list dashboards | Passed | Bootstrap log; guest token mint; `GET /api/v1/dashboard/` as the service account is 401/403 |
