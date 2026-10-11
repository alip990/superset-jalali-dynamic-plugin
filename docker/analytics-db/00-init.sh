#!/bin/bash
# Roles and the metadata database. Table grants live in 03-readonly-role.sql.
set -euo pipefail

escape() { printf "%s" "$1" | sed "s/'/''/g"; }
META_PW="$(escape "$SUPERSET_DB_PASSWORD")"
RO_PW="$(escape "$ANALYTICS_RO_PASSWORD")"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'superset') THEN
    CREATE ROLE superset LOGIN PASSWORD '${META_PW}';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'superset_ro') THEN
    CREATE ROLE superset_ro LOGIN PASSWORD '${RO_PW}';
  END IF;
END
\$\$;
SQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<'SQL'
SELECT 'CREATE DATABASE superset_meta OWNER superset'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'superset_meta')\gexec
SQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname superset_meta <<'SQL'
GRANT ALL PRIVILEGES ON DATABASE superset_meta TO superset;
SQL
