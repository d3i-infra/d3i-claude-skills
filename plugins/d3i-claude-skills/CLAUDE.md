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
- Skills target D3I coworkers, not one machine: use placeholders (`<username>`, `<workspace-ip>`, `<study>`) and GitHub URLs rather than personal paths, hostnames, or usernames

## Known Limitations

- `eyra-mono` references specific mono source files by path and line number; these drift as upstream changes, so verify against the current checkout before relying on a citation.
- `src-workspace-ops` is comprehensive but has not been through formal TDD skill testing yet.

The `write-adr` plugin moved out of this bundle to ship with the `adg` CLI
(`daniellemccool/ad-guidance-tool`, `tools/adr-plugin`); the marketplace references it
cross-repo. Update it there, not here.
