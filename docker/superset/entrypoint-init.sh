#!/bin/bash
# Create the metadata schema, the admin user, and FAB permissions. Idempotent.
set -euo pipefail

python - <<'PY'
import os
import socket
import time

def wait(host: str, port: int, label: str) -> None:
    for _ in range(60):
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"{label} is up", flush=True)
                return
        except OSError:
            time.sleep(1)
    raise SystemExit(f"{label} did not become reachable")

uri = os.environ["SUPERSET_METADATA_URI"]
# postgresql+psycopg2://user:pass@host:port/db
rest = uri.split("@", 1)[1]
host_port = rest.split("/", 1)[0]
host, port = host_port.split(":")
wait(host, int(port), "postgres")
redis = os.environ.get("REDIS_HOST", "redis")
wait(redis, 6379, "redis")
PY

superset db upgrade

set +e
superset fab create-admin \
  --username "$SUPERSET_ADMIN_USERNAME" \
  --firstname Admin \
  --lastname User \
  --email "$SUPERSET_ADMIN_EMAIL" \
  --password "$SUPERSET_ADMIN_PASSWORD"
status=$?
set -e
if [ "$status" -ne 0 ]; then
  echo "create-admin exited ${status}; continuing because the admin may already exist"
fi

superset init
echo "SUPERSET_INIT_DONE"
