#!/bin/sh
# ACEDRA backend container entrypoint: apply migrations, optionally seed synthetic demo data, start the API.
set -e
cd /app
echo "[acedra] Applying database migrations"
alembic upgrade head
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  echo "[acedra] SEED_DEMO_DATA=true — loading synthetic demo tenants if the database is empty"
  python database/seeds/seed_all.py --if-empty
fi
exec "$@"
