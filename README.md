# d3i-claude-skills

Claude Code plugin for the D3I data donation infrastructure team.

> **v0.2.0 — Early development.** These skills are actively being developed and tested. Expect changes.

## Skills

| Skill | Description | Status |
|-------|-------------|--------|
| `src-workspace-ops` | Debugging and managing D3I deployments on SURF Research Cloud | Early |
| `researcher-fork` | Working in a D3I researcher fork of data-donation-task | Migrated, needs path generalization |
| `eyra-mono` | Eyra Next (mono) platform architecture reference | Migrated, needs path generalization |

The `write-adr` plugin — ADR authoring and governance: durable **MADR** records,
compact **lean** records (with `applies_to` routing), and obeying injected ADR briefs
while editing code — ships with the `adg` CLI itself, at
[`daniellemccool/ad-guidance-tool`](https://github.com/daniellemccool/ad-guidance-tool)
under `tools/adr-plugin`, so its guidance tracks the tool in lockstep. This marketplace
references it cross-repo.

`adg` ships two ways. The plugin bundles a `bin/adg` wrapper that Claude Code puts on the
Bash tool's PATH, so the **authoring** skills fetch the matching CLI automatically — no
separate install. The **governance** path, however — the PreToolUse brief hook, the git
pre-commit hook, and CI (`adg lean index --root .`) — runs *outside* the plugin's PATH and
needs a **system `adg`**. Install it with the one-liner in the
[adg README](https://github.com/daniellemccool/ad-guidance-tool#install)
(`curl … | sh`). For the governance workflow (hook + CI), treat the system install as the
baseline; the ride-along is a convenience for the authoring skills.

## Installation

```bash
claude plugins add d3i-infra/d3i-claude-skills
```

## Local Testing

Test before pushing changes:

```bash
claude --plugin-dir /path/to/d3i-claude-skills
```

Reload after edits without restarting:
```
/reload-plugins
```

## Contributing

1. Branch from `main` using `feat/`, `fix/`, `chore/` prefixes
2. Test locally with `claude --plugin-dir .`
3. Open a PR with a description of what changed and why
4. **No secrets** — skills must never contain credentials, tokens, or API keys

See `CLAUDE.md` for full conventions.

## License

Apache-2.0
