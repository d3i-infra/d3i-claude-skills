---
name: src-workspace-ops
description: >
  Use when debugging, configuring, or managing a D3I data donation study running on
  SURF Research Cloud — workspace down, 502 errors, docker issues, storage/export
  problems, Research Drive setup, SSH access, or any SRC operational task.
---

# SRC Workspace Operations

Operational guide for D3I data donation deployments on SURF Research Cloud (SRC).

## How to Use This Skill

**You are a guide, not an operator.** SRC workspaces are remote servers that you cannot access. You cannot SSH into them, run docker commands, or execute anything on the workspace. All commands must be **given to the user to run**, and you must **wait for their output** before proceeding.

**Assume the user knows nothing.** They may not know what SSH is, how to open a terminal, what Docker does, or how any of this infrastructure works. When guiding them:

- **Explain every step before giving it.** Say what the command does and why, in plain language.
- **Give one step at a time.** Wait for the output before giving the next step.
- **Explain the output.** Tell them what it means — is it good or bad? What should they look for?
- **Define jargon when you first use it.** "SSH" = a way to connect to a remote server via your terminal. "Docker" = the system that runs the application in isolated containers. Etc.
- **Warn before anything destructive.** Editing config files, restarting services, pruning Docker — always explain what could go wrong first.
- **Never give multi-step command sequences.** Break them apart. One command, one explanation, one check.

### Information you need from the user first

Before you can help, you need to establish context. Ask for:

1. **Which workspace?** Name, hostname, or URL (e.g., `qself2026` or `https://qself2026.quantified-self.src.surf-hosted.nl`)
2. **What's the problem?** Site down, error message, can't export data, etc.
3. **Do they have SSH access?** Can they open a terminal and connect to the server? If not, guide them through the prerequisites below.

### Getting the user connected (SSH prerequisites)

If the user has never SSHed into an SRC workspace before:

1. **Find the workspace IP address**: Go to https://portal.live.surfresearchcloud.nl/, find the workspace, and look for the IP address in the workspace details.
2. **Find their SRC username**: In the SRC portal, click their name in the upper right corner → "My profile". Their username is shown there (e.g., `dmccool`).
3. **Open a terminal**:
   - macOS: Open the Terminal app (in Applications → Utilities)
   - Windows: Open PowerShell or install Windows Terminal from the Microsoft Store
   - Linux: Open your terminal emulator
4. **Connect**: Have them type `ssh <username>@<ip-address>` and press Enter. They may be asked to accept a fingerprint (type `yes`). If they get "Permission denied", their SSH key may not be registered in their SRC profile.
5. **Terminal compatibility**: If they get "Error opening terminal: xterm-kitty" or similar errors when running commands, have them run: `export TERM=xterm-256color`

Once connected, they'll see a prompt like `username@hostname:~$`. They're now on the workspace and can run commands you give them.

### How Docker works on these workspaces (explain to user as needed)

The data donation application runs inside "containers" — think of them as lightweight virtual computers running on the workspace. There are two:

- **self-d3i**: The main application (the website participants see)
- **db-next**: The database that stores all the study data

A program called **Docker** manages these containers. All Docker commands on the workspace require `sudo` (admin privileges) — the user just puts `sudo` in front of every command.

There's also a configuration file at `/docker-compose.yaml` that tells Docker how to run the containers — what settings to use, what ports to open, etc.

## Setting Up a New Workspace

If the user needs to create a new workspace for a study, guide them through `references/new-workspace.md`. The process involves:

1. **Create external storage first** — a persistent volume for backups and data (the workspace itself is volatile)
2. **Prepare parameters** — they'll need to generate a database password and secret key, choose an app name, and optionally set up Unsplash credentials. See `references/catalog-item.md` for the full parameter list.
3. **Create the workspace** in the SRC portal using the "Next for data donation" catalog item
4. **Wait for provisioning** (~10-15 minutes). If it fails, download logs from the portal.
5. **Post-setup**: SSH in, verify containers are running, configure Research Drive (`references/configure-research-drive.md`), set up database backups (`references/backup-database.md`), and deploy the correct data-donation-task version for the study (`references/update-workflow.md`)

Walk them through each phase one at a time. The runbooks have the detailed steps.

## Diagnosis Guide

Walk the user through these steps in order. **Give one step at a time and wait for their output.**

### Step 1: Is the workspace running?

Ask the user to check the SRC portal (https://portal.live.surfresearchcloud.nl/). The workspace should show state "running". If it shows "paused", they need to click Resume. If it shows "failed" or "unaccounted", see the SRC Portal Reference section below.

### Step 2: Can they connect?

Have them run:
```
ssh <username>@<ip-address>
```
If this hangs or fails, the workspace may be paused, failed, or their SSH key isn't set up. They cannot proceed without SSH access.

### Step 3: Are the containers running?

Once connected, have them run:
```
sudo docker ps
```

**Expected output**: Two containers listed — `self-d3i` and `db-next`, both with status "Up".

**If only `db-next` shows**: The application container is down. See "App container not running" below.

**If neither shows**: Both containers are down. See "Restarting everything" below.

### Step 4: Is the application responding?

Have them run:
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000
```

Explain: "This checks if the application is responding to web requests internally. It should print `200`."

- **200**: App is working. If the user is seeing errors in their browser, the problem is likely Nginx (the web server in front of the app) or authentication.
- **No output / hangs**: App may be starting up. Wait 30 seconds and try again.
- **Other codes (500, 502, etc.)**: App is having errors. Check the logs (Step 5).

### Step 5: Check the application logs

Have them run:
```
sudo docker logs self-d3i --tail=30
```

Explain: "This shows the last 30 lines of the application's log. Look for lines containing 'error' or 'ERROR'."

Share the output with you so you can interpret it.

## Common Issues and Fixes

### App container not running

**Explain to user**: "The application container isn't running. We need to start it. This command tells Docker to bring up all the containers defined in the configuration file."

Have them run:
```
sudo docker compose -f /docker-compose.yaml up -d
```

**If they get "project name must not be empty"**: This is a known issue on older workspaces. The configuration file is missing a name. Have them run this instead:
```
sudo COMPOSE_PROJECT_NAME=next docker compose -f /docker-compose.yaml up -d
```

Then to permanently fix it, have them edit the config file (explain that `nano` is a simple text editor):
```
export TERM=xterm-256color
sudo nano /docker-compose.yaml
```
Find the line that says `version: "3"` near the top and replace it with `name: "next"`. Save with Ctrl+O, Enter, then exit with Ctrl+X.

**After starting**, have them verify with `sudo docker ps` — both containers should show "Up".

### 502 Bad Gateway

**Explain to user**: "A '502 Bad Gateway' error means the web server (Nginx) is trying to forward your request to the application, but the application isn't responding. This usually means the application container is down."

Follow the same steps as "App container not running" above.

### Site loads but shows errors / donation workflow doesn't appear

This is likely an application-level issue, not infrastructure. Check the logs:
```
sudo docker logs self-d3i --tail=100
```

Look for errors related to:
- Missing environment variables
- Database connection failures
- Storage backend errors

### Export / download returns Internal Server Error

**Explain to user**: "The 'Export all' feature in the application only works when data is stored locally on the server. If the workspace is configured to send donated data to SurfDrive (which is the recommended setup), the export button will not work — this is a known limitation. Instead, the researcher should access their donated data by logging into https://surfdrive.surf.nl and looking in the folder that was configured for the study."

If they need to check which storage backend is active:
```
sudo docker inspect self-d3i --format '{{range .Config.Env}}{{println .}}{{end}}' | grep STORAGE
```

- If `STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_USER` is present → data goes to SurfDrive (export button won't work, this is expected)
- If no SURF_RESEARCH_DRIVE variables → data is stored locally in the container (export should work; if not, check logs)

### Disk full

**Explain to user**: "The workspace has a small disk (15 GB). Let's check how full it is."

```
df -h /
```

If it's over 90% full:
```
sudo docker system prune -f
```

**Warn first**: "This command cleans up unused Docker data (old images, stopped containers). It won't affect anything currently running, but I want you to know what it does before you run it."

## Configuring Research Drive (SurfDrive)

This is the setup that allows donated data to be automatically saved to the researcher's SurfDrive account. See `references/configure-research-drive.md` for the complete step-by-step runbook.

**High-level summary** (guide the user through each step individually):

1. The researcher creates an app password on https://surfdrive.surf.nl (Settings → Security → App passwords). They need to save the username, token, and WebDAV URL.
2. The researcher creates a folder on SurfDrive for the study data.
3. Someone with SSH access edits `/docker-compose.yaml` on the workspace to add the SurfDrive credentials as environment variables.
4. The application is restarted.
5. Test with a real donation to verify files appear on SurfDrive.

**Important**: The WebDAV URL varies. It may be `https://surfdrive.surf.nl/remote.php/dav/files/<username>/` or `https://surfdrive.surf.nl/files/remote.php/nonshib-webdav`. Use whatever the researcher provides.

**Do NOT set** `STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_PASSPHRASE` — the encryption code has a bug (encrypts but discards the result, writes unencrypted data).

## Technical Reference

### Architecture

```
Internet → Nginx (443, TLS + SRAM auth) → self-d3i (8000) → PostgreSQL (5432)
                                              ↓
                                         iframe: data-donation-task (React workflow)
                                              ↓ postMessage (MessageChannel API)
                                         CommandSystemDonate → storage backend
```

### Filesystem layout on the workspace

```
/
├── docker-compose.yaml        # Ansible-managed — the main config file
├── ca.crt                     # CA cert for DB TLS
├── server.crt, server.key     # PostgreSQL TLS certs
├── etc/nginx/
│   ├── conf.d/ssl_main.conf                    # Reverse proxy + TLS config
│   └── app-location-conf.d/authentication.conf # SRAM OAuth2 auth
└── home/<user>/
    └── data/
        ├── datasets/          # May contain study data
        ├── <volume-name>/     # Named external storage volume
        └── volume_2/          # Log archive
            ├── docker.log*    # App logs (rotated daily, gzipped)
            ├── nginx.log*     # Nginx logs (rotated daily, gzipped)
            └── system.log*    # System logs (rotated daily, gzipped)
```

### Key environment variables

From `/docker-compose.yaml` under `services.app.environment`:

| Variable | Purpose |
|----------|---------|
| `APP_NAME` | Workspace/study name |
| `APP_DOMAIN` | Public FQDN |
| `APP_ADMINS` | SRC username(s) with admin access |
| `DB_HOST` | Always `db` (Docker service name) |
| `DB_NAME`, `DB_USER`, `DB_PASS` | PostgreSQL credentials |
| `SECRET_KEY_BASE` | Cookie encryption key (≥64 chars) |
| `STATIC_PATH` | `/tmp` — where uploaded assets go |
| `STORAGE_SERVICES` | `builtin` (default) |
| `STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_*` | WebDAV credentials (if configured) |
| `DB_TLS_VERIFY` | `verify_peer` or `none` |

### Deployment background

The `/docker-compose.yaml` is generated by Ansible from the template in `d3i-infra/researchcloud-items` (`playbooks/deploy-next.yaml`). During provisioning, the Ansible playbook clones `d3i-infra/mono`, builds the Docker image from source, generates the compose file, and starts the containers. After provisioning, the source code is removed — only the built image remains.

### Known quirks

- **`$` in passwords**: If the database password contains `$`, Docker Compose treats `$foo` as a variable reference and replaces it with blank. Both containers get the same mangled value so auth works, but the password isn't what was originally entered. Fix: escape `$` as `$$` in the compose file.
- **`version: "3"` warning**: Deprecated Docker Compose syntax. Harmless warning, but replace with `name: "<app_name>"` to fix the project name issue.
- **latin1 locale warning in app logs**: The container lacks UTF-8 locale. Can be fixed by adding `ELIXIR_ERL_OPTIONS: "+fnu"` to the compose environment. Non-critical unless dealing with non-ASCII characters in donated data.
- **Banking.Fetcher "Fetched 0 payments"**: Normal. No payment integration is configured. This log message appears every 5 minutes and can be ignored.
- **Missing icon SVGs (404s for chatgpt.svg, linkedin.svg, etc.)**: Cosmetic — these icons aren't in the Docker image. Doesn't affect functionality.

### Database operations

```bash
# Connect to the database
sudo docker exec -it db-next psql -U my_user -d my_database

# Backup to external storage
sudo docker exec db-next pg_dump -U my_user my_database | gzip > ~/data/<volume>/db-$(date +%Y%m%d).sql.gz

# Restore from backup
zcat ~/data/<volume>/backup.sql.gz | sudo docker exec -i db-next psql -U my_user my_database
```

### Log access

| Log | Command |
|-----|---------|
| Live app logs | `sudo docker logs self-d3i --tail=100 -f` |
| Live DB logs | `sudo docker logs db-next --tail=50` |
| Historical app logs | `zcat ~/data/volume_2/docker.log.<date>.log.gz` |
| Historical nginx logs | `zcat ~/data/volume_2/nginx.log.<date>.log.gz` |
| Search for errors | `zgrep -i error ~/data/volume_2/docker.log.<date>*.gz` |
| SRC deployment logs | Download from SRC portal → Actions menu |

### SRC Portal reference

| Action | What it does |
|--------|-------------|
| Pause | Stops workspace, saves budget (CPU not charged while paused) |
| Resume | Restarts a paused workspace |
| Reboot | Pause + Resume. **Docker containers may not auto-restart after this.** |
| Delete | **Permanently destroys the workspace.** External storage volumes survive. |
| Download Detailed Logs | Ansible provisioning/deployment logs |

### Nginx authentication flow

SRAM OAuth2 (in `/etc/nginx/app-location-conf.d/authentication.conf`):
1. `/validate` checks `$cookie_authorization` against SRC gateway
2. If missing/invalid → redirect to SRC OAuth2 endpoint
3. On callback → token stored as cookie
4. `/admin` path requires auth; `/` path is open (app handles its own auth)

## Reference Files

This skill includes detailed reference documents. **Read these when you need deeper information** than what's in this SKILL.md.

**These reference files are written as technical docs — they contain bare commands and assume familiarity with the tools.** Adapt them to the user's level:
- If the user has been confidently running commands and interpreting output throughout the conversation, you can give them commands directly from the reference docs.
- If the user is still learning or has needed explanations for earlier steps, translate the reference docs into guided steps: explain what each command does, give one at a time, and interpret the output for them.

Gauge this from the conversation — the same user may need hand-holding for SSH but be comfortable once they're running docker commands.

| File | When to read it |
|------|----------------|
| [architecture.md](references/architecture.md) | Understanding the full system — iframe protocol, component stack, key source files |
| [deployment.md](references/deployment.md) | How provisioning works, the Ansible playbook, Docker Compose details, all operations commands |
| [debugging.md](references/debugging.md) | Comprehensive troubleshooting — all known issues with diagnosis steps and fixes |
| [ssh-and-access.md](references/ssh-and-access.md) | SSH connection details, web access URLs, SRAM/TOTP auth, firewall ports, CO roles |
| [storage.md](references/storage.md) | External storage volumes, Research Drive backends, data persistence strategy |
| [workspace-lifecycle.md](references/workspace-lifecycle.md) | Workspace states, pause/resume/delete behavior, error states, budget, expiration |
| [catalog-item.md](references/catalog-item.md) | "Next for data donation" catalog item — all components, interactive parameters, firewall rules |
| [configure-research-drive.md](references/configure-research-drive.md) | **Runbook**: Step-by-step SurfDrive WebDAV setup with troubleshooting |
| [new-workspace.md](references/new-workspace.md) | **Runbook**: Creating a new workspace from scratch — prerequisites, parameters, verification |
| [backup-database.md](references/backup-database.md) | **Runbook**: Manual and automated database backup, restore procedures |
| [update-workflow.md](references/update-workflow.md) | **Runbook**: Deploying a new version of the data-donation-task workflow |
