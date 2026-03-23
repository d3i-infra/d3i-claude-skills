# Catalog Item: Next for data donation

## Overview

"Next for data donation" is the SRC catalog item that deploys a complete data donation study environment.

**Description:** Deploys Next for hosting, configuring and managing a single data donation study.

**Documentation:** https://github.com/d3i-infra/mono

**Support:** Niek de Schipper (n.c.deschipper@uva.nl)

## Components

The catalog item is assembled from these SRC components, applied in order:

| Component | Purpose |
|-----------|---------|
| SRC-OS | Base Ubuntu 22.04 setup |
| SRC-CO | Collaborative Organisation user provisioning |
| SRC-Nginx | Reverse proxy with TLS and SRAM auth |
| SRC-External plugin | Runs Ansible for additional component setup |
| Next for data donation | Application deployment (mono + data-donation-task) |

## Cloud Settings

- **Provider:** SURF HPC Cloud
- **OS:** Ubuntu 22.04
- **Size:** 2 Core, 16 GB RAM
- **Boot disk:** 15 GB

## Interactive Parameters (set at workspace creation)

These are prompted when creating a workspace:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `app_name` | Display name for the application | `my-study` |
| `database_password` | PostgreSQL password | `un2eW9VCtQZxL5w` (pick something strong) |
| `secret_key_base` | Cookie encryption key, ≥64 chars | `aUMZobj7oJn58XIl...` |
| `surf_username` | Your SRC profile username | `dmccool` |
| `unsplash_access_key` | Unsplash API key for images | (from unsplash.com/developers) |
| `unsplash_app_name` | Unsplash app name | (the name you chose at unsplash) |

### Generating secret_key_base

```bash
openssl rand -base64 48
```

## Overwritable Parameters (defaults)

These have defaults but can be changed:

| Parameter | Source | Default | Description |
|-----------|--------|---------|-------------|
| `co_passwordless_sudo` | SRC-CO | `true` (overwritten) | Users get passwordless sudo |
| `co_research_drive` | SRC-CO | `true` | Research Drive integration enabled |
| `co_roles_enabled` | SRC-CO | `true` | CO role-based access |
| `co_totp` | SRC-CO | `true` | TOTP 2FA enabled |
| `co_admin_user_only` | SRC-CO | `false` | If true, only CO admins get accounts |
| `remote_ansible_version` | SRC-External plugin | `9.1.0` | Ansible version for deployment |
| `timeout` | SRC-External plugin | `3600` | Deployment timeout (seconds) |

## Access Rules (Firewall)

| From Port | To Port | IP | Direction | Protocol | Mutable |
|-----------|---------|-----|-----------|----------|---------|
| 22 | 22 | 0.0.0.0/0 | in | tcp | No |
| 80 | 80 | 0.0.0.0/0 | in | tcp | No |
| 443 | 443 | 0.0.0.0/0 | in | tcp | No |

All outbound traffic is allowed.

## Allowed Collaborative Organisations

- D3I data donation
- FMG Research Lab
- quantified-self-utwente

Visibility: **Available on request** (not public catalog).

## Budget

Estimated cost on SURF HPC Cloud:
- EINF: 48 cpu-hrs/day
- RCCS: 50.4 credits/day
