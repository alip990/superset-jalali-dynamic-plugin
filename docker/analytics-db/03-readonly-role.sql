-- superset_ro can read sales and nothing else. The role itself is created in 00-init.sh.
GRANT CONNECT ON DATABASE analytics TO superset_ro;
GRANT USAGE ON SCHEMA sales TO superset_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA sales TO superset_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA sales GRANT SELECT ON TABLES TO superset_ro;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA sales FROM PUBLIC;
GRANT USAGE ON SCHEMA sales TO superset_ro;
