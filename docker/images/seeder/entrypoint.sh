#!/bin/bash
# Seeder container entrypoint
# Environment variables are set by docker-compose.yml

set -euo pipefail

INDUSTRY="${DSK_INDUSTRY:?DSK_INDUSTRY must be set}"
SITE="${DSK_SITE:?DSK_SITE must be set}"
PHASE="${DSK_SEED_PHASE:-all}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-erpnext}"
SITE_ADMIN_PASSWORD="${SITE_ADMIN_PASSWORD:-admin}"

echo "==> demostackkit seeder"
echo "    Industry : $INDUSTRY"
echo "    Site     : $SITE"
echo "    Phase    : $PHASE"

# Wait for backend to be ready
MAX_WAIT=300
ELAPSED=0
echo "==> Waiting for backend..."
until curl -sf "http://backend:8000/api/method/ping" > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "ERROR: Backend not ready after ${MAX_WAIT}s"
        exit 1
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done
echo "==> Backend ready"

# Create site if it doesn't exist
BENCH="/home/frappe/frappe-bench"
if [ ! -f "$BENCH/sites/$SITE/site_config.json" ]; then
    echo "==> Creating site $SITE..."
    bench new-site "$SITE" \
        --mariadb-root-password "$DB_ROOT_PASSWORD" \
        --admin-password "$SITE_ADMIN_PASSWORD" \
        --no-mariadb-socket
    bench --site "$SITE" install-app erpnext
    echo "==> Site created"
else
    echo "==> Site $SITE already exists"
fi

# Run seeders via demostackkit CLI
echo "==> Running seeders (phase: $PHASE)..."
cd /demostackkit
demostackkit seed "$INDUSTRY" --phase "$PHASE"

echo "==> Seeding complete for $INDUSTRY"
