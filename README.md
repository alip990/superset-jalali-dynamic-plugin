# superset-jalali

Apache Superset 6.1.0, unchanged, with Jalali dates in dashboards that are embedded in our own app.

BI developers work in stock Superset. End users see the dashboard in an iframe. Charts, tables and pivots show Jalali labels such as `1403/07/18` and `1403-07 مهر`. The dashboard time filter is a Persian, Saturday-first calendar. Each app user gets a guest token whose row-level security clause limits rows by region. The analytical database is not modified: Superset connects as `superset_ro` and only runs `SELECT`.

Two mechanisms, kept separate:

- **Display and grouping.** Jinja macros in a virtual dataset add Jalali columns. The macros live in `superset-jalali-sql` and are registered as `JINJA_CONTEXT_ADDONS`.
- **Filtering.** A dynamic plugin replaces the dashboard time-range picker. It writes a normal Gregorian Superset time range, so indexes stay usable and saved dashboards still work if the plugin is turned off.

Superset 6.1 removed the dynamic-plugin list route. With `DYNAMIC_PLUGINS` on, a failed list request leaves every dashboard spinning. This stack registers a blueprint that serves that route and never returns an error. Do not enable the feature flag without the blueprint.

## Run it

```bash
cp .env.example .env   # change the secrets
make up                # docker compose up --build -d
```

Local ports, so this does not collide with a Superset already on 8088:

| Service | URL |
|---|---|
| Superset (admin) | http://localhost:8100 (`SUPERSET_PUBLISH_PORT`) |
| Host app | http://localhost:8101 |
| Postgres | 127.0.0.1:5444 |

Open the host app, pick a demo user, and the sales dashboard embeds with that user's region. `sara` sees the north, `reza` the south, `niloofar` the east, and `office` sees every region.

`make reset` drops volumes and starts clean. `make bootstrap` re-runs provisioning. `make test` runs the unit tests.

## What is provisioned

`bootstrap/bootstrap.py` is idempotent. It creates the `Analytics` connection as `superset_ro`, the `orders_jalali` virtual dataset, eight charts, the `sales-jalali` dashboard («داشبورد فروش»), four native filters, embedding for `HOST_APP_ORIGINS`, the `EmbedGuest` role, and the `guest_token_service` account. That account can grant guest tokens and nothing else.

Sample data lives in schema `sales` and covers Nowruz 1403 through 1405, including leap day 1403/12/30 (2025-03-20). About 150,000 orders.

## Packages

`packages/superset-jalali-sql` has no runtime dependencies. `tools/generate_nowruz.py` builds `nowruz.py` with `jdatetime==6.1.0` and `persiantools==4.0.0` and stops if they disagree. The running image does not import those libraries.

`packages/superset-jalali-datefilter` is the blueprint plus a small ES module. The Docker build runs the JS tests and refuses a bundle that contains a second React or gzips over 60 KB. Set `JALALI_DATEFILTER_BUNDLE=hello` to serve the Milestone 0 probe (a red button) instead of the calendar.

## Docs

- [Architecture](docs/architecture.md)
- [BI developer guide](docs/bi-developer-guide.md)
- [Operations](docs/operations.md)
- [Verified facts](docs/VERIFIED_FACTS.md)
