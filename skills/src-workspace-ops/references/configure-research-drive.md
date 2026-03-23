# Runbook: Configure Surf Research Drive for Donated Data

## Purpose

Configure mono to write donated data to SurfDrive via WebDAV so the researcher can access it. Without this, donated data is stored on LocalFS inside the Docker container volume — functional but inaccessible to the researcher and at risk of loss.

**Note:** This is a write-only integration. Mono PUTs each donation as a file to the SurfDrive folder. The researcher retrieves data by logging into surfdrive.surf.nl. The "Export all" button in the mono UI does NOT work with the Research Drive backend (it only works with LocalFS or S3).

## Steps

### 1. Researcher Creates SurfDrive App Credentials

The researcher (workspace owner) does this:

1. Go to https://surfdrive.surf.nl and log in with institutional account
2. Click the **gear icon** (top right) → **Settings**
3. Go to **Security** section
4. Scroll to **"App passwords / tokens"**
5. Enter a name (e.g., `qself2026`)
6. Click **Create new app password**
7. **Save all three values immediately** — they're shown only once:
   - **Username** — institutional ID format (e.g., `m7736653@utwente.nl`)
   - **Token** — the generated password
   - **WebDAV URL** — shown on the same page or in Settings → WebDAV. Format varies:
     - Personal: `https://surfdrive.surf.nl/remote.php/dav/files/<username>/`
     - Generic (for app tokens): `https://surfdrive.surf.nl/files/remote.php/nonshib-webdav`
   - Use whichever URL the researcher provides.

### 2. Researcher Creates a Folder on SurfDrive

On https://surfdrive.surf.nl, create a folder for this study's data (e.g., `qself2026-donations`).

### 3. Add Environment Variables to Docker Compose

SSH into the workspace:

```bash
ssh <username>@<ip>
export TERM=xterm-256color
```

Edit the compose file:

```bash
sudo nano /docker-compose.yaml
```

Add these under `services.app.environment` (alongside the existing env vars):

```yaml
      STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_USER: "<username-from-step-1>"
      STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_PASSWORD: "<token-from-step-1>"
      STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_URL: "https://surfdrive.surf.nl/files/remote.php/nonshib-webdav"
      STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_FOLDER: "<folder-name-from-step-2>"
```

**Do NOT set** `STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_PASSPHRASE` — the encryption code has a bug and the feature doesn't actually work.

### 4. Restart the Application

```bash
sudo COMPOSE_PROJECT_NAME=next docker compose -f /docker-compose.yaml up -d
```

### 5. Verify

```bash
# Check the app started
sudo docker ps

# Check logs for storage errors
sudo docker logs self-d3i --tail=30
```

Then have someone submit a test donation and check if the file appears on SurfDrive.

## Recovering Pre-Configuration Donations

Data donated before Research Drive was configured lives on LocalFS inside the Docker container:

```bash
# List files in the storage path
sudo docker exec self-d3i ls -la /tmp/

# Copy files out to the external storage volume
sudo docker cp self-d3i:/tmp/<files> ~/data/<volume>/
```

This data can then be manually uploaded to SurfDrive or shared with the researcher.

## How It Works

When a participant donates data:
1. Workflow sends `CommandSystemDonate {key, json_string}` via the iframe bridge
2. Mono receives it and calls `Storage.BuiltIn.SurfResearchDrive.store()`
3. The store function does an HTTP PUT to `<url>/<folder>/<filename>` with Basic Auth
4. The file appears on the researcher's SurfDrive

## Troubleshooting

### Donations not appearing on SurfDrive

```bash
# Check app logs during a donation
sudo docker logs -f self-d3i
# (have someone submit a donation, watch for errors)
```

Common issues:
- Wrong credentials → 401 error in logs
- Folder doesn't exist on SurfDrive → 404 or 409 error
- Wrong WebDAV URL → connection errors

### Test WebDAV connectivity from the workspace

```bash
# Test credentials and folder access
curl -u "<username>:<token>" -X PROPFIND \
  "https://surfdrive.surf.nl/files/remote.php/nonshib-webdav/<folder>/"
```

### After configuring, the "Export all" button still shows error

This is expected. The SurfResearchDrive backend's `list_files()` returns empty — it's write-only. The researcher accesses data directly via surfdrive.surf.nl, not the export button.
