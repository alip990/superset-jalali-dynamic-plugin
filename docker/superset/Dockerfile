# The JS bundle is built here. Superset's own frontend is not rebuilt.
FROM python:3.12-alpine@sha256:1b668429b3511ab407d8e00648891631b0b1a4d7e15e3ca70f38ab5b91ad4ab4 AS nowruz
WORKDIR /build
COPY packages/superset-jalali-sql /build/packages/superset-jalali-sql
COPY packages/superset-jalali-datefilter/frontend /build/packages/superset-jalali-datefilter/frontend
RUN python /build/packages/superset-jalali-datefilter/frontend/scripts/export_nowruz.py

FROM node:20-alpine@sha256:fb4cd12c85ee03686f6af5362a0b0d56d50c58a04632e6c0fb8363f609372293 AS datefilter
WORKDIR /build
COPY packages/superset-jalali-datefilter/frontend/package.json packages/superset-jalali-datefilter/frontend/package-lock.json ./
RUN npm ci
COPY packages/superset-jalali-datefilter/frontend/ ./
COPY --from=nowruz /build/packages/superset-jalali-datefilter/frontend/src/nowruz.generated.ts ./src/nowruz.generated.ts
COPY --from=nowruz /build/packages/superset-jalali-datefilter/frontend/test/fixtures/days.json ./test/fixtures/days.json
RUN npm test && OUT_DIR=/out npm run build

FROM apache/superset:6.1.0
USER root
RUN uv pip install --python /app/.venv/bin/python --no-cache psycopg2-binary==2.9.13
COPY packages/superset-jalali-sql /tmp/p/sql
COPY packages/superset-jalali-datefilter /tmp/p/datefilter
COPY --from=datefilter /out/ /tmp/p/datefilter/src/superset_jalali_datefilter/static/
COPY docker/superset/superset_config.py /app/pythonpath/superset_config.py
COPY docker/superset/entrypoint-init.sh /app/docker/entrypoint-init.sh
COPY bootstrap /app/bootstrap
RUN chmod 755 /app/docker/entrypoint-init.sh \
    && uv pip install --python /app/.venv/bin/python --no-cache /tmp/p/sql /tmp/p/datefilter \
    && rm -rf /tmp/p
USER superset
