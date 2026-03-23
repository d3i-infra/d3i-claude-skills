# D3I Workflow Engine — Log Interpretation Guide

## Architecture Overview

The D3I data donation task runs a Python workflow inside the browser using
Pyodide (Python compiled to WebAssembly). The architecture has these layers:

```
┌─────────────────────────────────────────────────┐
│  Host (Eyra/mono or GitHub Pages)               │
│  ├── [Feldspar] — donation fetch/storage        │
│  └── iframe containing the workflow             │
│       ├── ReactEngine — renders UI pages         │
│       ├── WorkerProcessingEngine — manages worker│
│       └── Web Worker (ProcessingWorker)          │
│            ├── Pyodide (Python in WASM)          │
│            └── port.* (Python workflow script)   │
└─────────────────────────────────────────────────┘
```

Communication flow:
1. Python script yields **commands** (render a page, donate data, log a message)
2. Worker sends commands to the main thread via `postMessage`
3. ReactEngine renders UI or Bridge forwards system commands to the host
4. User input flows back as **payloads** (string, file, JSON, void)

## Log Sources

| Source tag | What it is |
|-----------|-----------|
| `[ReactEngine]` | UI rendering — shows what pages are displayed and what payload came back |
| `[WorkerProcessingEngine]` | Worker lifecycle — started, received events from worker |
| `[ProcessingWorker]` | Inside the web worker — unwrap response, runCycle show the Python I/O |
| `[FakeBridge]` | Dev mode bridge — logs commands it can't handle (no real host) |
| `[LiveBridge]` | Production bridge — sends commands to Eyra host, reports donation status |
| `[Feldspar]` | Host-side (production only) — donation fetch start/complete/success |
| `pyodide.asm.js` with timestamp | Python-level log output from the workflow script |

## The Run Cycle

Each interaction with the user is a "run cycle":

1. Python yields a `CommandUIRender` with a page to display
2. `WorkerProcessingEngine` receives `runCycleDone` from worker
3. `ReactEngine` renders the page and waits for user input
4. User interacts → response wrapped as a Payload type
5. `ProcessingWorker` receives `nextRunCycle` with the response
6. `ProcessingWorker` unwraps the payload and feeds it to Python
7. Python processes and yields the next command → back to step 1

In the logs, one cycle looks like:
```
[WorkerProcessingEngine] Received event from worker: runCycleDone
[ReactEngine] received: event {__type__: 'CommandUIRender', page: {…}}
[ProcessingWorker] unwrap response: {"__type__":"PayloadString","value":"..."}
[ProcessingWorker] runCycle {"__type__":"PayloadString","value":"..."}
```

## Command Types

| Command | Meaning |
|---------|---------|
| `CommandUIRender` | Display a UI page (forms, file upload, consent, results, error) |
| `CommandSystemEvent` | Lifecycle event sent to host (e.g., `"initialized"`) |
| `CommandSystemDonate` | Send donated data to host for storage (production only) |
| `CommandSystemLog` | Structured log message sent to host (appears in server logs too) |

## Payload Types

| Payload | Meaning |
|---------|---------|
| `PayloadString` | Text input — platform selection, button clicks ("continue") |
| `PayloadFile` | File upload — the user's data package (.zip) |
| `PayloadJSON` | Processed data tables — the extracted/transformed donation data |
| `PayloadVoid` | No-op acknowledgment — user clicked continue with no data to send |

## Page Types (in CommandUIRender)

| Page `__type__` | What the user sees |
|----------------|-------------------|
| `PropsUIPageDonation` | Main donation flow page (file upload, extraction progress) |
| `PropsUIPageEnd` | Thank you / completion page |
| `PropsUIPageError` | Python error page with stack trace |
| (Radio/Check inputs) | Platform selection menu |

## Bridge Modes

### FakeBridge (local development / GitHub Pages)

- No real host — runs standalone
- `CommandSystemDonate` is logged but data goes nowhere
- `CommandSystemEvent` logged as "received unknown command"
- Good for testing the workflow flow, but donations are not persisted
- Identified by: `Running with fake bridge` at startup

### LiveBridge (deployed on Eyra/mono)

- Connected to the Eyra host via iframe postMessage
- `CommandSystemDonate` sends data to the server
- `[Feldspar]` lines show host-side donation handling
- `[LiveBridge] DonateSuccess` confirms server accepted the data
- `[LiveBridge] Donation completed, pending: 0` means all platforms done
- Identified by: `[LiveBridge]` lines in the log

## Common Flow: Multi-Platform Donation

A typical production session with multiple platforms (e.g., Facebook +
Instagram + LinkedIn):

```
1. Init: Pyodide loads → packages → port installed → initialiseDone
2. CommandSystemEvent("initialized") → host knows workflow is ready
3. Platform selection page rendered (RadioInput)
4. For each platform:
   a. "Starting platform: X" (CommandSystemLog)
   b. File upload page → user provides .zip
   c. "File received: N bytes" (CommandSystemLog)
   d. "Validation: valid (json_en)" (CommandSystemLog)
   e. "Extraction complete: N tables, M rows" (CommandSystemLog)
   f. Consent form shown → user accepts
   g. "Consent: accepted" (CommandSystemLog)
   h. "Donation started: payload size=N bytes" (CommandSystemLog)
   i. CommandSystemDonate with key and data
   j. [Feldspar] Donate starting → success
   k. "Donation result: success" (CommandSystemLog)
5. Final page / thank you
```

## Debugging Checklist

When investigating a problem in a log:

- [ ] Check the metadata header — any errors detected?
- [ ] Did `initialiseDone` appear? If not, Pyodide failed to load
- [ ] What mode? FakeBridge can't actually donate data
- [ ] Look for `PropsUIPageError` — Python crash with stack trace
- [ ] Look for `ERROR` in Python log lines
- [ ] Count `CommandUIRender` events — does the number of pages match expectations?
- [ ] For donation issues: look for `CommandSystemDonate` and `DonateSuccess`
- [ ] For extraction issues: look for `Extraction complete` log messages
- [ ] For consent issues: look for `Consent form shown` and `Consent: accepted`
- [ ] Check timing between first and last timestamp — unusually long gaps may indicate the user left and came back
