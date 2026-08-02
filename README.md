# d3i-claude-skills

Claude Code **plugin marketplace** for the D3I data donation infrastructure team. It
contains two plugins (note that the first shares its name with the marketplace itself):

| Plugin | Contents | Who needs it |
|--------|----------|--------------|
| `d3i-claude-skills` | SRC workspace ops + Eyra mono architecture skills (lives in this repo) | D3I infra work |
| `write-adr` | ADR authoring + governance skills (lives in [`daniellemccool/ad-guidance-tool`](https://github.com/daniellemccool/ad-guidance-tool), referenced cross-repo) | Anyone writing ADRs |

> **v0.2.0 — Early development.** These skills are actively being developed and tested. Expect changes.

## Skills

The `d3i-claude-skills` plugin provides:

| Skill | Description | Status |
|-------|-------------|--------|
| `src-workspace-ops` | Debugging and managing D3I deployments on SURF Research Cloud | Active |
| `eyra-mono` | Eyra Next (mono) platform architecture reference | Active |

The `write-adr` plugin provides ADR authoring and governance: durable **MADR** records,
compact **lean** records (with `applies_to` routing), and obeying injected ADR briefs
while editing code. It ships with the `adg` CLI itself, at
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

Installing is a two-step process: first register the marketplace (this tells Claude Code
where to find the plugins), then install the plugin(s) you want from it.

```bash
# 1. Register the marketplace (once per machine)
claude plugin marketplace add d3i-infra/d3i-claude-skills

# 2. Install one or both plugins
claude plugin install d3i-claude-skills   # D3I infra skills
claude plugin install write-adr           # ADR authoring + governance
```

If a plugin name exists in more than one registered marketplace, disambiguate with
`<plugin>@<marketplace>`, e.g. `claude plugin install write-adr@d3i-claude-skills`.

Both commands can also be run from inside a Claude Code session via the interactive
`/plugin` menu, or by asking Claude — though note that sandboxed sessions may block
writes to `~/.claude/plugins`, in which case run the commands in your own terminal.

Useful maintenance commands:

```bash
claude plugin list                  # show installed plugins
claude plugin marketplace list      # show registered marketplaces
claude plugin marketplace update d3i-claude-skills   # refresh the marketplace listing
claude plugin update <plugin>       # update an installed plugin (restart to apply)
claude plugin uninstall <plugin>    # remove a plugin
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
