# Runbook: Creating a New Workspace

## Prerequisites

- [ ] SRC account with access to the relevant CO
- [ ] Budget/wallet with sufficient credits
- [ ] External storage volume created (see storage.md)
- [ ] Unsplash API key (optional, for images)

## Steps

### 1. Create External Storage (if not already done)

1. SRC portal → CREATE NEW (storage card)
2. Select SURF HPC Cloud volume
3. Select the correct CO (must match workspace CO)
4. Choose size (50 GB is the standard for data donation)
5. Name it meaningfully (e.g., `<study-name>`)

### 2. Prepare Parameters

Before starting, have these ready:

| Parameter | How to generate |
|-----------|----------------|
| `app_name` | Choose a descriptive name for the study |
| `database_password` | `openssl rand -base64 16` |
| `secret_key_base` | `openssl rand -base64 48` |
| `surf_username` | Your SRC profile → My Profile |
| `unsplash_access_key` | From unsplash.com/developers |
| `unsplash_app_name` | The app name you chose at Unsplash |

**Save these values somewhere secure.** You won't see them again after workspace creation.

### 3. Create the Workspace

1. SRC portal → CREATE NEW (workspace card)
2. Select **"Next for data donation"** catalog item
3. Select your CO
4. Select wallet
5. Choose **SURF HPC Cloud**, **Ubuntu 22.04**, **2 Core - 16 GB RAM**
6. Fill in the interactive parameters from step 2
7. **Attach the storage volume** (second-to-last step)
8. Set an appropriate expiration date
9. Review and submit

### 4. Wait for Deployment

Deployment takes ~10-15 minutes. Monitor in the SRC portal.

If it fails:
- Download detailed logs (Actions → Download Detailed Logs)
- Check the bottom of the log for errors
- Common fix: just retry (transient network/capacity issues)

### 5. Verify the Workspace

Once running:

```bash
# SSH in
ssh <username>@<ip-from-portal>

# Check services
docker compose ps

# Check the web URL
curl -I https://<hostname>.<co>.src.surf-hosted.nl
```

### 6. Post-Setup Checklist

- [ ] Verify external storage is mounted at `~/data/<volume-name>`
- [ ] Verify the web UI is accessible
- [ ] Verify SRAM authentication works
- [ ] Configure storage backend (Research Drive or external volume path)
- [ ] Set up initial database backup schedule
- [ ] Deploy the correct data-donation-task version for the study
- [ ] Test a donation flow end-to-end

## Record Keeping

After creation, record the following in the relevant study documentation:

- Workspace ID
- Hostname and URL
- IP address
- CO name
- Storage volume ID and name
- Expiration date
- Owner
