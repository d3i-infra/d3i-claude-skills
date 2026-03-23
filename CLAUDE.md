# CLAUDE.md

## What this is

A Claude Code plugin containing skills for the D3I data donation infrastructure team. Skills are reference guides that Claude Code loads to help users with specific tasks.

## Principles

- **Skills guide users, they don't act.** The `src-workspace-ops` skill in particular works with remote servers that Claude cannot access. All commands are given to the user to run. Other skills may be more hands-on depending on context.
- **No secrets in this repo.** Skills and reference docs must never contain credentials, tokens, passwords, or API keys. Use placeholders like `<username>`, `<token>`, etc.
- **Adapt to the user's level.** Reference docs are technical. Skills should instruct the agent to gauge the user's comfort and explain accordingly.

## Structure

```
skills/
  <skill-name>/
    SKILL.md              # Main skill file (required)
    references/           # Supporting docs the agent can consult
    assets/               # Templates, scripts
    evals/                # Test scenarios (if any)
```

## Contributing

- Branch from `main`, use `feat/`, `fix/`, `chore/` prefixes
- Keep SKILL.md descriptions focused on triggering conditions (when to use), not workflow summaries
- Test locally with `claude --plugin-dir .` before submitting a PR
- The `researcher-fork` and `eyra-mono` skills contain hardcoded paths from the original author's machine — these should be generalized over time

## Known Limitations

- `researcher-fork` and `eyra-mono` were migrated from personal commands. Hardcoded paths have been replaced with relative references and GitHub URLs, but some assumptions about directory layout remain (e.g., `d3i/forks/<researcher>/<repo>`).
- `write-adr` depends on the `adg` tool being installed in the project. It was designed for use within `data-donation-task`.
- `src-workspace-ops` is comprehensive but has not been through formal TDD skill testing yet.
