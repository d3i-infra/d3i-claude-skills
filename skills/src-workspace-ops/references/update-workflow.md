# Runbook: Updating the Data Donation Workflow

## When

When a researcher fork or d3i-infra/data-donation-task has been updated and the changes need to be deployed to a running SRC workspace.

## Steps

### 1. SSH into the workspace

```bash
ssh <username>@<ip>
```

### 2. Back up the database first

Follow the [backup-database.md](backup-database.md) runbook.

### 3. Update the workflow code

```bash
cd ~/path/to/data-donation-task

# Check current state
git status
git log --oneline -5

# Pull latest changes
git pull origin <branch>
```

### 4. Rebuild

```bash
pnpm install
pnpm run build
```

### 5. Deploy to mono

Copy the built workflow assets to mono's static assets directory:

```bash
# The exact path depends on the workspace setup
# Check where mono expects feldspar assets:
ls ~/path/to/mono/core/priv/static/feldspar/

# Copy new build
cp -r packages/feldspar/dist/* ~/path/to/mono/core/priv/static/feldspar/
```

### 6. Restart mono (if needed)

```bash
cd ~/path/to/mono
docker compose restart app
```

### 7. Verify

1. Open the study URL in a browser
2. Start a data donation flow
3. Verify the workflow loads and functions correctly
4. Check for JavaScript console errors (F12)
5. Test a full donation submission

## Rollback

If something goes wrong:

```bash
# Check git log for previous version
cd ~/path/to/data-donation-task
git log --oneline -10

# Revert to previous commit
git checkout <previous-commit-sha>

# Rebuild and redeploy (steps 4-6)
```
