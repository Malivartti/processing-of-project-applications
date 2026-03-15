#!/usr/bin/env sh
set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="${BACKUP_DIR}/ppa_${TIMESTAMP}.dump.gz"

echo "[$(date)] Starting backup..."

pg_dump \
  -h "${POSTGRES_HOST:-db}" \
  -U "${POSTGRES_USER:-ppa}" \
  -d "${POSTGRES_DB:-ppa_db}" \
  -Fc \
  | gzip > "${FILENAME}"

echo "[$(date)] Backup saved: ${FILENAME}"

# Delete backups older than 30 days
find "${BACKUP_DIR}" -name "ppa_*.dump.gz" -mtime +30 -delete
echo "[$(date)] Old backups cleaned (>30 days)"
