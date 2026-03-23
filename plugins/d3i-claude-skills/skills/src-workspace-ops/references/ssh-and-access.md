# SSH and Access

## SSH Access

### Connection

```bash
ssh <username>@<workspace-ip>
```

Example:
```bash
ssh dmccool@145.38.204.74
```

- **Username**: Your SRC profile username. Find it under "My profile" in the upper right corner of the SRC portal.
- **IP address**: Shown in the workspace details in the SRC portal.
- **Port**: 22 (standard SSH, open by default)

### Authentication

SSH key-based authentication. Your SSH public key must be registered in your SRC profile (uploaded via SRAM or the SRC portal).

### Passwordless sudo

Enabled by default on D3I workspaces (`co_passwordless_sudo: true`). You can run:
```bash
sudo <command>
```
without entering a password.

## Web Access

### Participant/Researcher URL

```
https://<hostname>.<co-slug>.src.surf-hosted.nl
```

Example:
```
https://qself2026.quantified-self.src.surf-hosted.nl
```

This URL is shown in the workspace details. Nginx handles TLS termination and SRAM-based authentication.

### SRC Portal

```
https://portal.live.surfresearchcloud.nl/
```

Login via your institution (SRAM) or EduID. Provides workspace management, storage, and billing.

## Authentication Methods (for web UI)

| Method | Description |
|--------|-------------|
| SRAM | Preferred. Uses institutional or EduID credentials. |
| TOTP | Time-based one-time password. Alternative 2FA method. |

## SRAM / Collaborative Organisation

Access to a workspace requires membership in the corresponding Collaborative Organisation (CO) in SRAM. The CO controls:
- Who can log into the workspace web UI (via Nginx's `rsc_nginx_co_role`)
- Who gets user accounts on the workspace (SSH access)
- Which storage and catalog items are available

### CO Admin Role

Members of the `src-co-admin` group within a CO can be restricted as the only users provisioned on the workspace (if `co_admin_user_only` is set to `true`; default is `false`).

## Open Ports

| Port | Direction | Protocol | Purpose |
|------|-----------|----------|---------|
| 22 | inbound | TCP | SSH |
| 80 | inbound | TCP | HTTP (redirects to 443) |
| 443 | inbound | TCP | HTTPS |

All outbound traffic is allowed by default.

## TOTP Setup

TOTP is enabled by default (`co_totp: true`). Users may need to configure a TOTP app (e.g., Google Authenticator) when first accessing the workspace via the web UI through SRAM.
