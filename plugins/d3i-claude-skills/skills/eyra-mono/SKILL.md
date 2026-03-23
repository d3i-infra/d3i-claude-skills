---
name: eyra-mono
description: >
  Use when working on questions that touch the Eyra Next (mono) platform — assignment model,
  consent system, donation storage and file naming, panel_info, iframe lifecycle, and how
  researcher forks integrate with the host.
---

# Eyra mono architecture reference

Load this context when working on questions that touch the Eyra Next platform:
how assignments work, how donations are stored, how consent gating behaves,
or how a researcher fork integrates with mono.

The upstream mono repo is at https://github.com/eyra/mono (typically cloned to `eyra/mono` within a D3I workspace layout). The production branch is `develop`.

---

## UI terminology → code mapping

| Next UI label | Mono concept | Key file |
|---|---|---|
| Project | `Project` | `systems/project/` |
| Item | `Assignment` (`Assignment.Model`) | `systems/assignment/` |
| Workflow (within an Item) | `Workflow` with ordered `WorkflowItem`s | `systems/workflow/` |
| Flow application (per workflow) | `Feldspar.Tool` — a zip archive served as an iframe | `systems/feldspar/` |
| Participant link | `/a/<token>?p=participant_id` — handled by `Assignment.Controller` | `systems/assignment/controller.ex` |

One Item = one invite link. Multiple workflow items within an Item are completed
in sequence by every participant.

---

## Participant flow (state machine)

`crew_page_builder.ex` — `current_view/2` determines what a participant sees.

On first visit (`initial_view`):
1. Intro page (if assignment has an info page ref and user hasn't visited it)
2. Consent page (if `consent_signed?` returns false)
3. Email activation (non-tester only, if account not activated)
4. Work view (the feldspar task loop)

On subsequent visits: if `tasks_finished?` → finished page. Otherwise work view.

**Consent gating** (`crew_page_builder.ex:167`):
- `consent_agreement: nil` → always signed (no consent required)
- Non-tester: signed if *any* signature exists — persists forever across sessions
- Tester/preview: signed only if signature matches the *latest* revision — requires
  re-signing after consent document updates, which is why repeated preview runs
  produce no onboarding file

---

## Onboarding file

When a participant accepts or declines consent, `crew_page.ex:102` calls:

```elixir
store(socket, onboarding_identifier(socket), "{\"status\":\"consent accepted\"}")
```

`onboarding_identifier` (`crew_page.ex:166`) builds:
```
[:assignment, id], [:participant, ""], [:key, "<session_id>-onboarding"]
```

No `task` or `source` segment → filename: `assignment=X_participant=Y_key=<sid>-onboarding.json`

**This fires at most once per participant per assignment** (or per consent revision
for preview users). Repeated preview sessions on the same assignment produce no
onboarding file.

---

## Donation file naming

`feldspar/controller.ex:256` — `build_meta_data` composes the identifier:

```elixir
[:assignment, assignment_id],
[:task,        context["task"]],          # workflow_item_id
[:participant, context["participant"]],
[:source,      context["group"]],         # lowercased icon name
[:key,         key]                       # e.g. "<session_id>-linkedin"
```

`context["group"]` is set in `feldspar/tool_view_builder.ex:52` from the
workflow item's **icon name** (lowercased). This is the `source=` segment in
filenames and is the platform identifier within a multi-workflow Item.

Example filename:
```
assignment=89_task=1066_participant=preview_source=x_key=1772814964320-x.json
```

---

## Task completion

`crew_task_single_view.ex:64` — when the Feldspar script reaches `PropsUIPageEnd`:
```elixir
Crew.Public.complete_task(task)   # status → :completed
publish_event(:work_done)         # → finished_view
```

`finished_states` = `[:completed, :accepted, :rejected]` (`crew/task_status.ex`).

Once `:completed`, subsequent visits show the finished page immediately —
participants cannot re-run the task. **Exception**: if a participant abandons
mid-session (browser closed before PageEnd), the task stays `:pending` and they
can start over on the next visit, which may produce a second donation file for
the same platform with no mechanism to invalidate the first.

---

## panel_info

Built in `assignment/controller.ex:254` when the participant first hits the invite link:

```elixir
%{panel: :next, redirect_url: nil, participant: participant}
```

**Custom URL parameters** (e.g. `&d=abc123`) are **not captured** into `panel_info`.
They are forwarded only to external redirect systems (Qualtrics etc.) via the
Integration tab, not to the Python script.

`panel_info` is available in the Feldspar upload context and is stored with each
donation, but is **not** currently passed to `firstRunCycle` or the Python script.

---

## Routing participants to a single platform

Options (no mono changes required):

**A — Separate Items per platform** (recommended):
Create one Item per platform, each with one workflow item and its own invite link.
Upload the corresponding per-platform build (see the `release.sh` pattern in the researcher-fork skill).
Send each participant the link for their platform's Item.

**B — Wire `group` through to the script** (requires mono PR):
`context["group"]` (the icon/platform name) is already in the upload context.
Thread it through `worker_engine.ts → py_worker.js → main.py → script.py`
(same pattern as `VITE_PLATFORM`). One Item, one build, runtime routing.

**C — Capture `&d=` into panel_info** (requires mono PR):
Add `&d=LinkedIn` to the invite link and capture it in `add_panel_info`.
Pass it through to the script. Most flexible for panel-based routing.

---

## Donation HTTP flow (feldspar_app.js → controller.ex)

As of early 2026, donations use **HTTP POST** (not WebSocket):

1. **feldspar_app.js** receives `CommandSystemDonate` via MessageChannel port1
2. Builds `FormData` with `key`, `context` (JSON upload context), and `data` (Blob)
3. POSTs to `/api/feldspar/donate`
4. **controller.ex** validates auth, stores file via `DataDonationFolder.store()`,
   schedules async delivery via `Storage.Public.deliver_file()`
5. Returns JSON: `{"status": "ok"}` or error

**Response contract** (sent back to iframe via port1.postMessage):
- `{ __type__: "DonateSuccess", key: string, status: number }` — on HTTP 2xx
- `{ __type__: "DonateError", key: string, status: number, error: string }` — on HTTP error or network failure (status=0 for offline/timeout)

**WaitGroup for exit ordering**: `feldspar_app.js` tracks in-flight donations
via a `WaitGroup`. When `CommandSystemExit` arrives, `waitForDonationsAndExit()`
awaits all pending donations before forwarding the exit event to LiveView. This
prevents data loss when the script finishes before large uploads complete.

---

## Logging infrastructure

`CommandSystemLog` is handled via HTTP, not WebSocket:

1. **feldspar_app.js** `handleLogCommand()` parses `json_string` field
2. POSTs to `/api/feldspar/log` with level, message, and merged upload context
   (assignment_id, task, participant, etc.)
3. Routed to Elixir Logger → AppSignal for observability

feldspar_app.js also sends its own operational logs (donate start/success/error,
exit events) via the same `sendLog()` helper.

---

## Iframe lifecycle (feldspar_app.js hook)

The `FeldsparApp` Phoenix LiveView hook manages the iframe:

1. **Mount**: Creates iframe, sets `src` from `data-src` attribute (archive URL + `/index.html`)
2. **app-loaded**: Iframe posts `{ action: 'app-loaded' }` → host creates `MessageChannel`,
   sends `{ action: 'live-init', locale }` with `port2` to iframe via `postMessage`
3. **Legacy onload**: Also listens for iframe `load` event for older feldspar versions
   (pre-2025-04-30). `setupChannel()` guards against double initialization.
4. **Resize**: Iframe sends `{ action: 'resize', height }` → host resizes iframe element
5. **Communication**: All subsequent command traffic flows through the MessageChannel ports
   (port1 on host, port2 in iframe)

**Upload context** (`data-upload-context` attribute): JSON containing assignment_id,
task (workflow_item_id), participant, group (icon name). Merged into log context
and donation metadata.

---

## d3i-infra/mono differences

d3i-infra/mono (https://github.com/d3i-infra/mono, typically cloned to `d3i-infra/mono`) is a stripped-down fork for
SURF Research Cloud deployments:

| Feature | eyra/mono | d3i-infra/mono |
|---|---|---|
| Donation transport | HTTP POST to `/api/feldspar/donate` | **Not implemented** — commands flash "Unsupported" |
| Log transport | HTTP POST to `/api/feldspar/log` | **Not implemented** |
| Storage backend | S3, Azure Blob, etc. | SURF Research Drive (WebDAV + Basic Auth) |
| Authentication | Google Sign-In | nginx external auth (`NginxLoginSurf`) |
| Donation queuing | WaitGroup + async delivery scheduling | None |
| Cleanup jobs | `DataDonationCleanupWorker` via Oban | None |

**Implication for Python code**: d3i-infra/mono returns `PayloadVoid` for donate
commands (fire-and-forget), while eyra/mono returns `PayloadResponse` with
success/failure via the LiveBridge. `handle_donate_result()` must handle both.

---

## Key source files

| Concept | File |
|---|---|
| Assignment state machine | `core/systems/assignment/crew_page_builder.ex` |
| Consent gating | `core/systems/assignment/crew_page_builder.ex:167` |
| Onboarding store call | `core/systems/assignment/crew_page.ex:97` |
| Task completion | `core/systems/assignment/crew_task_single_view.ex:64` |
| Donation HTTP endpoint | `core/systems/feldspar/controller.ex` |
| Filename composition | `core/systems/feldspar/controller.ex:256` |
| Upload context (group/icon) | `core/systems/feldspar/tool_view_builder.ex:52` |
| panel_info construction | `core/systems/assignment/controller.ex:254` |
| Task finished states | `core/systems/crew/task_status.ex` |
| Iframe hook (JS) | `core/assets/js/feldspar_app.js` |
| Iframe hook tests | `core/assets/js/feldspar_app.test.js` |
| WaitGroup (donate ordering) | `core/assets/js/wait_group.js` |
| Feldspar routes | `core/systems/feldspar/_routes.ex` |
| Data donation folder | `core/systems/feldspar/data_donation_folder.ex` |
| Tool view (LiveView) | `core/systems/feldspar/tool_view.ex` |
| App view (iframe render) | `core/systems/feldspar/app_view.ex` |
| Tool view builder (context) | `core/systems/feldspar/tool_view_builder.ex` |
