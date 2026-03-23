---
name: ingest-devlog
description: >
  Efficiently ingest and analyze browser developer console logs from D3I data
  donation tasks. Use this skill whenever the user shares a .log file from the
  browser dev console, mentions "console log", "dev console", "devtools log",
  references files like ddt*.log, or asks to check/debug/verify a data donation
  task run. Also use when the user says things like "I saved the console output",
  "here's the log from the browser", or "check what happened in this session".
  These logs are extremely token-heavy due to base64 worker scripts and WASM
  stack traces — always preprocess before reading.
---

# Ingest D3I Dev Console Logs

Browser console logs from D3I data donation tasks contain a mix of highly
informative workflow events buried in massive noise (base64 worker scripts,
WASM stack traces, pyodide internals). A 164-line log can be 80K+ tokens raw
but contain only ~25 meaningful lines. This skill prevents wasting context
window and tool calls on noise.

## Procedure

### Step 1: Preprocess with the cleaning script

Run the bundled script on the log file before reading any of its content.
Reading the raw log directly will waste enormous amounts of context on noise.

```bash
python <skill-path>/scripts/clean_devlog.py <logfile>
```

The script:
- Strips base64 worker URLs (~4,300 chars each, repeated 10-20x per log)
- Strips WASM/pyodide stack traces (dozens of frames per Python log line)
- Removes redundant engine event lines (3 lines per cycle → 1)
- Collapses consecutive PayloadVoid cycles into summaries
- Truncates large JSON payloads to 300 chars with type hints
- Strips build-specific JS file prefixes (hash changes per deploy)
- Extracts metadata: bridge mode, port, platforms, timestamps, errors
- Preserves original line numbers for cross-referencing

Output includes a header with session metadata followed by numbered signal
lines. For a typical log, expect 90-99% reduction.

Use `--save` to write a `.cleaned.log` file alongside the original — useful
when comparing multiple logs or when the user may want to revisit.

### Step 2: Read the cleaned output

For small logs (cleaned output < 100 lines): read the full output.

For large logs (cleaned output > 100 lines): read the header first to
understand the session, then use Grep on the cleaned output for the user's
specific concern. Common grep targets:
- `ERROR` or `PropsUIPageError` — errors
- `[FakeBridge]` or `[LiveBridge]` — host communication
- `CommandSystemDonate` — donation events
- `CommandSystemLog` — Python-level flow messages
- `Consent` — consent form events
- A specific platform name like `[Facebook]` or `[LinkedIn]`

### Step 3: Interpret and respond

See `references/workflow-engine-logs.md` for the D3I workflow engine
architecture. Key points for quick interpretation:

**Normal flow looks like:**
1. Init → Pyodide loads packages → `initialiseDone`
2. `CommandSystemEvent("initialized")` sent to bridge
3. Series of `runCycleDone` → `CommandUIRender` pairs (each is a page shown)
4. Python INFO lines show what the workflow is doing
5. `CommandSystemDonate` with a key and data (production only)
6. Final render cycles for thank-you/completion pages

**Red flags:**
- `PropsUIPageError` — Python crashed, check the stacktrace field
- `ERROR` in Python log lines
- Missing `CommandSystemDonate` when donation was expected
- `initialiseDone` never appearing (Pyodide failed to load)
- `[FakeBridge] received unknown command:` for commands other than
  `CommandSystemEvent` — FakeBridge can't handle donations

**FakeBridge vs LiveBridge:**
- FakeBridge = local dev / GitHub Pages (no real host, donations are logged
  but not stored)
- LiveBridge = deployed on Eyra/mono (donations are sent to the server,
  `[Feldspar]` lines show host-side status)

### When the user asks about PayloadJSON content

PayloadJSON lines contain actual donated data and are truncated by default.
If the user specifically asks to examine the data content:
1. Note the original line number from the cleaned output
2. Read that specific line range from the *original* raw log file
3. The JSON is typically double-escaped — parse carefully

Do not read PayloadJSON content unless explicitly asked. It's large, often
sensitive (participant data), and rarely relevant to debugging.

## Comparing multiple logs

When the user wants to compare two sessions (e.g., ddt14 vs ddt15):
1. Run the cleaning script with `--save` on both logs
2. Read both cleaned outputs
3. Compare the event sequences — focus on where they diverge
4. The metadata headers make quick comparison easy (mode, platforms, errors)
