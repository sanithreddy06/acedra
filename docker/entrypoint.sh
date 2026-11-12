#!/bin/sh
# ACEDRA backend container entrypoint: apply migrations, optionally seed sample data (never in production),
# start the API.
set -e
cd /app
# Fail before touching the database if the configuration is not acceptable for this environment.
python -c "import app.core.config" || { echo "[acedra] Invalid configuration; not starting." >&2; exit 1; }
echo "[acedra] Applying database migrations"
alembic upgrade head
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  echo "[acedra] SEED_DEMO_DATA=true - loading sample universities if the database is empty"
  python database/seeds/seed_all.py --if-empty
fi
exec "$@"
