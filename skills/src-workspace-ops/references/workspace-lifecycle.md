# Workspace Lifecycle

## States

```
Creating → Running ↔ Paused → Deleted
              ↓          ↓
           Failed    Unhealthy
              ↓
          Unaccounted (budget depleted)
```

## Actions

### Pause

Temporarily stops the workspace. **Budget is preserved** — CPU/GPU credits are not consumed while paused. Storage charges may still apply depending on wallet type:
- RCCS contracts: storage is charged while paused
- Grant-based wallets: storage is not charged while paused

**Before pausing:**
- Stop all data processing
- Ensure no users are logged in
- Failing to do so may cause unpredictable behavior

External storage volumes remain attached but can be detached while paused.

### Resume

Restarts a paused workspace. Transitions through `resuming` state before returning to `running`. Persistent storage automatically reattaches.

### Reboot

Executes pause + resume consecutively. Use after:
- System updates
- Configuration changes
- Process restarts needed

### Delete

**Permanently removes the workspace. No recovery.**

- External storage volumes are NOT deleted (they persist independently)
- All workspace-local data is lost
- Docker volumes, application state, database — all gone

### Claim Ownership

Available to `src_ws_admin` group members. Allows taking over workspace ownership when the previous owner leaves.

### Download Detailed Logs

Available via the Actions menu. Provides deployment logs — especially useful when workspaces fail during creation.

## Data Persistence

**Workspaces are volatile.** When deleted, everything is gone.

What persists:
- External storage volumes (attached via `~/data/<volume-name>`)
- Data pushed to Research Drive
- Data stored in external S3/Azure

What does NOT persist:
- Workspace filesystem (except attached volumes)
- Docker volumes (unless on external storage)
- Application state, databases
- Configuration changes made on the workspace

**Always ensure critical data (database dumps, donated data, configs) is on external storage or backed up externally.**

## Error States

### Failed

Workspace failed during provisioning or execution.

**To diagnose:**
1. Go to workspace in the SRC portal
2. Actions → Download log files
3. Check the bottom of the log for the error

**Common causes:**

| Error | Cause | Fix |
|-------|-------|-----|
| SSH connection timeout | Network/capacity issue | Retry later |
| OpenStack instance error | Cloud capacity unavailable | Retry later; contact Service Desk if persistent |
| Ansible task failure | Component script error | Review logs; contact Service Desk |

### Unhealthy

Unexpected condition. Service Desk is automatically notified. No user action required — they will correct the state.

### Unaccounted

Budget/wallet credits depleted. Workspace cannot resume until credits are replenished.

**Recovery:**
- Check wallet status in SRC portal
- RCCS: contact contract owner for credits
- NWO grants: apply for extension

## Expiration

Workspaces have an expiration date set at creation. After expiration, the workspace is automatically deleted. Monitor this in workspace details.

## Budget Estimation

The "Next for data donation" catalog item on SURF HPC Cloud costs approximately:
- **EINF**: 48 cpu-hrs/day
- **RCCS**: 50.4 credits/day
