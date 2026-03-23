---
name: researcher-fork
description: >
  Use when working in a D3I researcher fork of data-donation-task — project structure,
  per-platform build and deploy pattern, received-file validation, upstream relationship
  to d3i-infra, and release workflow.
---

# D3I researcher fork reference

Load this context when working in a researcher fork of `d3i-infra/data-donation-task` (or `eyra/feldspar`).
These forks are typically found under `forks/<researcher>/<repo>` in a D3I workspace layout and
contain study-specific Python scripts and configuration.

---

## Repo structure

```
packages/
  feldspar/          # Feldspar UI framework (TypeScript/React) — usually unmodified
  data-collector/    # Host app for local dev and building the deployable zip
    public/
      py_worker.js   # Pyodide web worker — bridges JS firstRunCycle → Python start()
  python/
    port/
      script.py      # Main study script — defines platform sequence and donation flow
      main.py        # Entry point called by py_worker.js — start(sessionId, platform)
      platforms/     # One module per platform (linkedin.py, x.py, instagram.py, …)
      helpers/       # Shared extraction and validation utilities
    tests/
      validate_received.py   # Interactive received-file validation (see below)
      test_dataframe_truncation.py
release.sh           # Per-platform build loop (see below)
```

---

## Toolchain

- **JS**: pnpm (monorepo). Install if missing: `npm install -g pnpm`
- **Python**: poetry. Tests and builds run inside `packages/python/`.
- **Build**: `pnpm run build` — builds Python wheel, feldspar, and data-collector
- **Dev**: `pnpm start` — watch mode for local testing
- **Release**: `pnpm run release` — per-platform production builds (see below)

---

## Per-platform build and deploy pattern

`release.sh` loops over an explicit platform list, sets `VITE_PLATFORM` per iteration,
builds the full app, and zips `packages/data-collector/dist/`:

```bash
platforms=("LinkedIn" "X")   # keep in sync with active platforms in script.py

for PLATFORM in "${platforms[@]}"; do
    export VITE_PLATFORM=$PLATFORM
    pnpm run build
    # → releases/dd-vu-2026_LinkedIn_<branch>_<date>_<nr>.zip
done
```

**VITE_PLATFORM wiring** (as of dd-vu-2026):
- `worker_engine.ts` reads `import.meta.env.VITE_PLATFORM`, sends in `firstRunCycle`
- `py_worker.js` passes it to `port.start(sessionId, platform)`
- `main.py` forwards to `process(session_id, platform)`
- `script.py` filters `all_platforms` list; unknown/missing platform runs all

Each zip is uploaded to a separate **Item** in Eyra Next (one per platform).
See `/eyra-mono` for how Items, workflows, and invite links relate.

**Branch name sanitisation**: `release.sh` replaces `/` with `-` in the branch name
before using it in the zip filename, to avoid path errors on feature branches.

---

## Deploying to Eyra

1. Run `pnpm run release` → zips appear in `releases/`
2. In Eyra Next: open the Item for that platform → workflow item → upload the zip
3. Each platform's Item has its own invite link: `https://next.eyra.co/a/<token>?p=participant_id`
4. Send participants the link for their assigned platform

Received files are delivered to the storage endpoint configured in the project's
Integration tab and arrive in `~/data/d3i/test_packages/<study>/received_files/<date>/`.

---

## Received file naming

Files are named by Eyra using these segments (see `/eyra-mono` for full detail):
```
assignment=<id>_task=<workflow_item_id>_participant=<id>_source=<icon>_key=<session_id>-<platform>.json
```

`source=` comes from the Eyra workflow item's icon name (lowercased).
`key=` suffix (e.g. `-linkedin`, `-x`) comes from what the Python script passes to `ph.donate()`.

**Onboarding files** (`*-onboarding.json`) are only generated on a participant's first
session per assignment (or after a consent document revision). Absent on repeat runs.

---

## Validating received files

Interactive script — discovers platforms, prompts for expected outcome, validates:

```fish
cd packages/python
poetry run python tests/validate_received.py \
    --received-dir ~/data/d3i/test_packages/<study>/received_files/<date>
```

Prompts:
- Which platforms to test (Enter = all found)
- Per platform: `consent` / `consent-with-change` / `decline`

Validates schema (tables, columns) and deleted row counts against known schemas
for LinkedIn and X. Unknown platforms skip column checks but still validate structure.

**Note**: the originating DDP zips and received files contain personal data and are
never committed. They live in `~/data/d3i/test_packages/`.

---

## Adding a new platform

1. Uncomment (or add) the platform in `script.py`'s `all_platforms` list
2. Add the platform name to `platforms=` in `release.sh`
3. Add the platform schema to `SCHEMAS` in `tests/validate_received.py`
4. Deploy and validate with `validate_received.py`

---

## Upstream relationship and pending upstreams

```
eyra/feldspar
    └── d3i-infra/data-donation-task   (Claude Code must never push here directly)
            └── <researcher>/<fork>    ← researcher's working fork
```

Changes developed and tested in a researcher fork flow upstream via PR to
`d3i-infra/data-donation-task` once proven in a live study. Never push directly
to d3i-infra repos.

**Patterns that may be upstreamed to d3i-infra/data-donation-task** (originated in researcher forks):
- Per-platform release pattern (`release.sh` loop + `VITE_PLATFORM` wiring)
- `PayloadFile` / `AsyncFileAdapter` support in `py_worker.js` and `main.py`
- `validate_received.py` interactive validation script
- Multi-platform `script.py` architecture
