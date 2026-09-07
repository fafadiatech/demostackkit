#!/bin/bash
# Write common_site_config.json for Frappe bench.
# Called by the configurator container on first startup.
set -e

CONFIG_FILE="/home/frappe/frappe-bench/sites/common_site_config.json"

# host_name must be reachable from inside the backend container. wkhtmltopdf
# (Print → PDF) fetches CSS/assets via get_url(); without this it builds
# http://<site>.localhost which does not resolve on the Docker network
# (HostNotFoundError). frontend:8080 is the nginx service on the compose network.
# See https://github.com/frappe/frappe_docker/issues/1547
cat > "$CONFIG_FILE" <<EOF
{
  "db_host": "${DB_HOST}",
  "db_port": ${DB_PORT},
  "redis_cache": "redis://${REDIS_CACHE}",
  "redis_queue": "redis://${REDIS_QUEUE}",
  "redis_socketio": "redis://${REDIS_QUEUE}",
  "socketio_port": 9000,
  "host_name": "http://frontend:8080"
}
EOF

echo "common_site_config.json written:"
cat "$CONFIG_FILE"
