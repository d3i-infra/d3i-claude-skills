# Storage

## External Storage Volumes

External storage volumes persist beyond workspace lifecycles. They are the primary mechanism for keeping data safe.

### Mount Point

Attached volumes are mounted at:
```
~/data/<volume-name>
```

The volume name is sanitized for use in the path.

### Creating a Volume

1. In SRC portal, click **CREATE NEW** on the storage card
2. Select cloud provider storage solution
3. Select your **Collaborative Organisation** (must match the workspace's CO)
4. Choose billing wallet
5. Select storage type (options depend on CO memberships)
6. Configure size (larger = more budget consumed)
7. Name the volume, review, accept terms, submit

### Attaching to a Workspace

**At creation time:** Select the volume in the second-to-last step of workspace creation.

**After creation (post-Feb 2024):**
1. **Pause** the workspace first
2. Go to the workspace's **Storage** tab
3. Click **+** to attach an available volume

**Constraints:**
- Volume and workspace must be in the **same CO**
- Volume and workspace must be on the **same cloud provider**
- A volume can only be attached to **one workspace at a time**
- Oracle cloud does not support post-creation attach/detach

### Detaching

1. Pause the workspace
2. Go to Storage tab
3. Click the unlink icon

### Deletion

**Deleting a volume permanently removes all data.** There is no recovery.

Deleting a *workspace* does NOT delete attached volumes — they return to "available" state.

## Data Persistence Strategy for D3I

On a running D3I workspace, the following data needs to persist:

| Data | Default Location | Risk | Mitigation |
|------|-----------------|------|------------|
| PostgreSQL database | Workspace filesystem | Lost on delete | Regular pg_dump to external storage |
| Donated data files | Storage backend (configured) | Depends on backend | Use Research Drive or external storage |
| Application config | Workspace filesystem | Lost on delete | Document in this ops base; version control |
| Docker volumes | Workspace filesystem | Lost on delete | Store DB data dir on external volume |
| SSL/TLS certs | Managed by SRC Nginx | Auto-managed | N/A |

### Recommended Setup

1. Attach an external storage volume to the workspace
2. Configure PostgreSQL data directory or regular dumps to `~/data/<volume>`
3. Configure mono's storage backend to write donated data to Research Drive or a path on the external volume
4. Keep configuration files version-controlled in this repo

## Surf Research Drive

mono supports Surf Research Drive as a storage backend (WebDAV-based). Configured via environment variables:

```
STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_USER=<username>
STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_PASSWORD=<password>
STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_URL=<webdav-url>
STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_FOLDER=<folder>
```

Research Drive is enabled at the workspace level via `co_research_drive: true` (default for D3I workspaces).

## Storage Backend Options in mono

Configured via `STORAGE_SERVICES` environment variable:

| Backend | Config Prefix | Notes |
|---------|--------------|-------|
| Surf Research Drive | `STORAGE_BUILTIN_SURF_RESEARCH_DRIVE_*` | WebDAV, recommended for SRC |
| AWS S3 | `AWS_*`, `STORAGE_S3_PREFIX` | Standard S3 |
| Azure Blob | `AZURE_*` | Azure storage |
| LocalFS | (default path) | Workspace-local, volatile |
