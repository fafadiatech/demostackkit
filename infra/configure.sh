#!/bin/bash
# Write common_site_config.json for Frappe bench.
# Called by the configurator container on first startup.
set -e

CONFIG_FILE="/home/frappe/frappe-bench/sites/common_site_config.json"

cat > "$CONFIG_FILE" <<EOF
{
  "db_host": "${DB_HOST}",
  "db_port": ${DB_PORT},
  "redis_cache": "redis://${REDIS_CACHE}",
  "redis_queue": "redis://${REDIS_QUEUE}",
  "redis_socketio": "redis://${REDIS_QUEUE}",
  "socketio_port": 9000
}
EOF

echo "common_site_config.json written:"
cat "$CONFIG_FILE"
