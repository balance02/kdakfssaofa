#!/usr/bin/env bash
set -euo pipefail
DIR=/var/backups/db
mkdir -p "$DIR"
docker compose -f /opt/uncensored-ai/docker-compose.yml exec -T db \
  pg_dump -U app app | gzip > "$DIR/app-$(date +%F-%H%M).sql.gz"
find "$DIR" -name '*.sql.gz' -mtime +7 -delete