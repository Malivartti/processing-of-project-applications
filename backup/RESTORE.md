# Database Restore Guide

## List available backups

```bash
docker compose exec backup ls /backups/
```

Or on host if you have a local mount:
```bash
ls -lh backups/
```

## Restore to the running database

```bash
# Replace <backup_file> with the actual filename, e.g. ppa_20260315_030001.dump.gz
docker compose exec -T backup \
  sh -c "gunzip -c /backups/<backup_file> | pg_restore \
    -h db \
    -U \${POSTGRES_USER} \
    -d \${POSTGRES_DB} \
    --clean --if-exists --no-owner --no-privileges"
```

## Restore to a separate test database

```bash
# 1. Create test DB
docker compose exec db psql -U ppa -c "CREATE DATABASE ppa_restore_test;"

# 2. Restore
docker compose exec -T backup \
  sh -c "gunzip -c /backups/<backup_file> | pg_restore \
    -h db \
    -U ppa \
    -d ppa_restore_test \
    --no-owner --no-privileges"
```

## Manual backup (without waiting for cron)

```bash
docker compose exec backup /backup.sh
```

## Backup schedule

Backups run daily at **03:00 (UTC)** via crond inside the `backup` container.
Files older than **30 days** are automatically deleted.

## Backup file format

`ppa_YYYYMMDD_HHMMSS.dump.gz` — PostgreSQL custom-format dump, gzip-compressed.
