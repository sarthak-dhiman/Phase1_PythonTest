#!/bin/sh
set -e

# Wait for Postgres to be ready (30s max)
retry=0
until pg_isready -h "${PG_HOST:-localhost}" -p "${PG_PORT:-5432}" -U "${PG_USER:-root}" >/dev/null 2>&1 || [ $retry -ge 30 ]; do
  echo "Waiting for postgres... ($retry)"
  sleep 1
  retry=$((retry+1))
done

# Default to async runtime URL; alembic/env.py will swap to psycopg2 when needed
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://root:root@${PG_HOST:-localhost}:${PG_PORT:-5432}/chicmic}"

# Run migrations (dev convenience). Non-fatal here.
alembic -c alembic.ini upgrade head || echo "Alembic failed, continuing..."

exec uvicorn api_server:app --host 0.0.0.0 --port 8000
