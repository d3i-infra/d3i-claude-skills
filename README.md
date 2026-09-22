# d3i-claude-skills

Claude Code **plugin marketplace** for the D3I data donation infrastructure team. It
contains two plugins (note that the first shares its name with the marketplace itself):

| Plugin | Contents | Who needs it |
|--------|----------|--------------|
| `d3i-claude-skills` | SRC workspace ops + Eyra mono architecture skills (lives in this repo) | D3I infra work |
| `write-adr` | ADR authoring + governance skills (lives in [`d3i-infra/adg`](https://github.com/d3i-infra/adg), referenced cross-repo) | Anyone writing ADRs |

> **v0.2.0 — Early development.** These skills are actively being developed and tested. Expect changes.

## Skills

The `d3i-claude-skills` plugin provides:

| Skill | Description | Status |
|-------|-------------|--------|
| `src-workspace-ops` | Debugging and managing D3I deployments on SURF Research Cloud | Active |
| `eyra-mono` | Eyra Next (mono) platform architecture reference | Active |

The `write-adr` plugin provides ADR authoring and governance: compact **lean** records (with
`applies_to` routing), compiled briefs injected by hooks, and obeying those briefs while editing
code. It ships in the `adg` repo, [`d3i-infra/adg`](https://github.com/d3i-infra/adg) under
`tools/adr-plugin`, so its guidance tracks the tool in lockstep. This marketplace references it
cross-repo.

`adg` is a system dependency that the plugin does not bundle. The plugin's hooks and skills
call `adg` as a bare command, so it has to be on your `PATH`: see the
[install section of the adg README](https://github.com/d3i-infra/adg#install). In a repo with
`docs/decisions/`, the plugin's session-start hook tells you when `adg` is missing or out of
date.

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
