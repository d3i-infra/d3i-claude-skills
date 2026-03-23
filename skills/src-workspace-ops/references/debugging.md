# Debugging Guide

## Quick Diagnosis Checklist

When something is wrong, work through this in order:

1. **Is the workspace running?** Check SRC portal → workspace state
2. **Can you SSH in?** `ssh dmccool@<ip>` — if not, workspace may be paused/failed
3. **Are Docker containers up?** `docker compose ps`
4. **Is the app responding?** `curl -I http://localhost:4000`
5. **Is Nginx proxying correctly?** `curl -I https://<domain>` from outside
6. **Are there application errors?** `docker compose logs -f app`
7. **Is the database healthy?** `docker compose exec db pg_dump -U postgres -l`

## Common Issues

### Workspace won't start / stuck in "creating"

**Symptoms:** Workspace stays in "creating" state or transitions to "failed"

**Actions:**
1. Download detailed logs from SRC portal (Actions → Download Detailed Logs)
2. Check bottom of log for error message
3. Common causes:
   - SSH timeout → transient network issue, retry
   - OpenStack error → capacity issue, retry later
   - Ansible failure → component script bug, contact Service Desk

### Site unreachable (HTTPS)

**Symptoms:** Browser shows connection error or timeout

**Check order:**
```bash
# 1. Is the workspace running? (check SRC portal)

# 2. SSH in and check services
docker compose ps                          # app and db should be "Up"
sudo systemctl status nginx                # nginx should be active

# 3. Check nginx can reach the app
curl -I http://localhost:4000              # should return 200

# 4. Check nginx config
sudo nginx -t                              # should say "ok"

# 5. Check TLS cert
echo | openssl s_client -connect localhost:443 2>/dev/null | head -5
```

### 502 Bad Gateway

**Symptoms:** Nginx returns 502

**Cause:** Nginx can't reach the upstream (mono app)

```bash
# Is the app container running?
docker compose ps app

# Check app logs for crash
docker compose logs --tail=100 app

# Restart the app
docker compose restart app
```

### Application crashes / container restarts

**Symptoms:** App container in restart loop or exited

```bash
# Check exit code and logs
docker compose ps
docker compose logs --tail=200 app

# Common causes:
# - Missing environment variables
# - Database connection failure
# - Secret key base not set or too short
# - Port conflict
```

### "project name must not be empty"

**Symptoms:** `docker compose` commands fail with "project name must not be empty"

**Cause:** Docker Compose derives the project name from the directory name. At `/`, the directory name is empty. The original Ansible template used `version: "3"` (deprecated) and had no `name:` field.

**Proper fix:** Edit `/docker-compose.yaml` and replace the `version: "3"` line with `name: "next"` (or the appropriate project name). This has been fixed in the Ansible template for new workspaces.

**Workaround (old workspaces):** Prefix all compose commands with `COMPOSE_PROJECT_NAME=next`:
```bash
sudo COMPOSE_PROJECT_NAME=next docker compose -f /docker-compose.yaml <command>
```

### Database connection errors

**Symptoms:** App logs show "connection refused" or TLS errors to PostgreSQL

```bash
# Is DB container running?
docker compose ps db

# Can you connect directly?
docker compose exec db psql -U postgres -l

# Check DB logs
docker compose logs --tail=100 db

# TLS issues? Try disabling TLS verification
# Set DB_TLS_VERIFY=none in docker-compose environment
```

### Iframe / workflow not loading

**Symptoms:** The data donation workflow doesn't appear in the study page

**Check order:**
1. Browser console (F12) for JavaScript errors
2. Check if feldspar assets are present in mono's static directory
3. Check for CORS or Content-Security-Policy headers blocking the iframe
4. Verify the workflow build was successful

```bash
# Check if feldspar assets exist
ls -la ~/path/to/mono/core/priv/static/feldspar/

# Check app logs for feldspar-related errors
docker compose logs app | grep -i feldspar
```

### Donation data not being stored

**Symptoms:** Participants complete the workflow but no data appears

**Check:**
```bash
# Check storage backend config
docker compose exec app env | grep STORAGE

# Check app logs during a donation attempt
docker compose logs -f app
# (then have someone submit a donation)

# If using Research Drive, check WebDAV connectivity
curl -u <user>:<pass> -X PROPFIND <webdav-url>

# If using LocalFS, check the storage directory
ls -la ~/path/to/storage/
```

### Workspace running out of disk

**Symptoms:** Operations fail, "no space left on device" errors

```bash
# Check disk usage
df -h

# Find large files/directories
du -sh /* 2>/dev/null | sort -rh | head -20
du -sh /var/lib/docker/* 2>/dev/null | sort -rh | head -10

# Docker cleanup (removes unused images/containers/volumes)
docker system prune -f

# Check if DB WAL files are accumulating
docker compose exec db du -sh /var/lib/postgresql/data/pg_wal/
```

Boot disk is only **15 GB** — this is tight. Large Docker images or unmanaged logs can fill it quickly.

### `$` in passwords (docker-compose variable substitution)

**Symptoms:** Docker Compose shows warnings like `WARN[0000] The "foo" variable is not set. Defaulting to a blank string.` when starting containers.

**Cause:** If `database_password` or any other Ansible parameter contains `$`, Ansible writes it literally into `/docker-compose.yaml`. Docker Compose then interprets `$foo` as variable substitution (e.g., `p@$$w0rd` becomes `p@w0rd` because `$$` becomes `$` and `$w0rd` is treated as an empty variable).

**Why it still works (usually):** Both the app and the DB containers get the same mangled value from the same compose file, so authentication succeeds. But the actual password in use is not what was originally entered.

**Fix:** Escape `$` as `$$` in `/docker-compose.yaml`, or avoid `$` in passwords when creating workspaces.

### Terminal: "Error opening terminal: xterm-kitty"

**Symptoms:** Commands like `less`, `nano`, or anything using ncurses fail with "Error opening terminal: xterm-kitty"

**Cause:** The kitty terminal sets `TERM=xterm-kitty`, which is not in the server's terminfo database.

**Fix:**
```bash
export TERM=xterm-256color
```

### Budget/credits depleted

**Symptoms:** Workspace enters "unaccounted" state, cannot be resumed

**Actions:**
1. Check wallet status in SRC portal
2. Contact wallet/contract owner for more credits
3. For NWO grants: apply for extension

### After workspace reboot, services don't start

**Symptoms:** Workspace is running but app is down after pause/resume

```bash
# Check if Docker daemon is running
sudo systemctl status docker

# Start Docker if needed
sudo systemctl start docker

# Bring up the stack
cd ~/path/to/mono
docker compose up -d

# Check if services started
docker compose ps
```

## Log Locations

| Log | How to access |
|-----|--------------|
| mono app logs | `docker compose logs -f app` |
| PostgreSQL logs | `docker compose logs -f db` |
| Nginx access log | `sudo tail -f /var/log/nginx/access.log` |
| Nginx error log | `sudo tail -f /var/log/nginx/error.log` |
| System log | `sudo journalctl -f` |
| SRC deployment logs | Download from SRC portal (Actions menu) |

## Useful One-Liners

```bash
# Current resource usage
free -h && echo "---" && df -h / && echo "---" && docker stats --no-stream

# All listening ports
sudo ss -tlnp

# Recent app errors only
docker compose logs --since=1h app 2>&1 | grep -iE "error|exception|crash"

# Database size
docker compose exec db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('next_dev'));"

# Active database connections
docker compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Check if external storage is mounted
mount | grep data
```
