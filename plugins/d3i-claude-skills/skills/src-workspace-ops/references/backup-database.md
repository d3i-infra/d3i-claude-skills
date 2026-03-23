# Runbook: Database Backup

## Why

The PostgreSQL database runs on the workspace filesystem, which is volatile. If the workspace is deleted or fails unrecoverably, the database is lost. Regular backups to external storage are essential.

## Manual Backup

```bash
# SSH into the workspace
ssh <username>@<ip>

# Create a backup directory on external storage
mkdir -p ~/data/<volume-name>/db-backups

# Dump the database
docker compose exec -T db pg_dump -U postgres next_dev | gzip > ~/data/<volume-name>/db-backups/next_dev_$(date +%Y%m%d_%H%M%S).sql.gz
```

## Verify Backup

```bash
# Check the backup file exists and has reasonable size
ls -lh ~/data/<volume-name>/db-backups/

# Optionally verify it can be read
zcat ~/data/<volume-name>/db-backups/next_dev_<timestamp>.sql.gz | head -20
```

## Automated Backup (cron)

```bash
# Add a daily backup cron job
crontab -e

# Add this line (runs daily at 3 AM):
0 3 * * * cd ~/path/to/mono && docker compose exec -T db pg_dump -U postgres next_dev | gzip > ~/data/<volume-name>/db-backups/next_dev_$(date +\%Y\%m\%d_\%H\%M\%S).sql.gz

# Also add cleanup to keep only last 30 days:
0 4 * * * find ~/data/<volume-name>/db-backups/ -name "*.sql.gz" -mtime +30 -delete
```

## Restore from Backup

```bash
# Stop the app (to prevent writes during restore)
docker compose stop app

# Restore
zcat ~/data/<volume-name>/db-backups/next_dev_<timestamp>.sql.gz | docker compose exec -T db psql -U postgres next_dev

# If the database needs to be recreated first:
docker compose exec db psql -U postgres -c "DROP DATABASE next_dev;"
docker compose exec db psql -U postgres -c "CREATE DATABASE next_dev;"
zcat ~/data/<volume-name>/db-backups/next_dev_<timestamp>.sql.gz | docker compose exec -T db psql -U postgres next_dev

# Restart the app
docker compose start app
```
