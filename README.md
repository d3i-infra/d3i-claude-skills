# d3i-claude-skills

Claude Code plugin marketplace for the D3I data donation infrastructure team.

> **v0.1.0 — Early development.** These skills are actively being developed and tested. Expect changes.

## Plugins

### d3i-claude-skills

Skills for D3I infrastructure operations, researcher fork workflows, and documentation.

| Skill | Description | Status |
|-------|-------------|--------|
| `src-workspace-ops` | Debugging and managing D3I deployments on SURF Research Cloud | Early |
| `researcher-fork` | Working in a D3I researcher fork of data-donation-task | Migrated |
| `eyra-mono` | Eyra Next (mono) platform architecture reference | Migrated |
| `write-adr` | Creating Architectural Decision Records with MADR/adg | Migrated |
| `ingest-devlog` | Efficiently ingest browser dev console logs from D3I data donation tasks | Early |

## Installation

### Step 1: Add the marketplace

In a Claude Code session:
```
/plugin marketplace add d3i-infra/d3i-claude-skills
```

### Step 2: Install the plugin

```
/plugin install d3i-claude-skills@d3i-infra/d3i-claude-skills
```

## Local Testing

Test before pushing changes:

```bash
claude --plugin-dir /path/to/d3i-claude-skills/plugins/d3i-claude-skills
```

Reload after edits without restarting:
```
/reload-plugins
```

## Contributing

1. Branch from `main` using `feat/`, `fix/`, `chore/` prefixes
2. Test locally with `claude --plugin-dir`
3. Open a PR with a description of what changed and why
4. **No secrets** — skills must never contain credentials, tokens, or API keys

See `plugins/d3i-claude-skills/CLAUDE.md` for full conventions.

## License

Apache-2.0
