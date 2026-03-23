#!/usr/bin/env python3
"""Clean D3I browser dev console logs for efficient analysis.

Strips noise (base64 worker URLs, WASM stack traces, pyodide internals,
redundant engine events) and truncates large payloads, producing a compact
event timeline with original line numbers preserved.

Usage:
    python clean_devlog.py <logfile> [--save]
"""

import sys
import re
import argparse
from pathlib import Path


# ──────────────────────────────────────────────
# Noise patterns — lines matching any of these are dropped entirely
# ──────────────────────────────────────────────

NOISE_PATTERNS = [
    # Base64-encoded worker script URLs (biggest token waster: ~4300 chars each)
    re.compile(r"data:text/javascript;base64,"),
    # WASM/Pyodide stack frames (covers $func*, $Py*, $_Py*, _PyCFunction*, etc.)
    re.compile(r"^\$\w+\s*@\s*pyodide\.asm"),
    re.compile(r"^_\w+\s*@\s*pyodide\.asm"),
    re.compile(
        r"^(batched|write|doWritev|handleEAGAIN|readWriteHelper)\s*@\s*pyodide"
    ),
    re.compile(r"^\(anonymous\)\s*@\s*(pyodide|data:text/javascript|py_worker|d3i_py_worker)"),
    re.compile(r"^Module\.\w+\s*@\s*pyodide"),
    # Bare stack frame fragments (no @ source — appear between WASM frames)
    re.compile(r"^(apply|Promise\.then)\s*$"),
    re.compile(r"^(apply|Promise\.then)\s*@"),
    # Stack frames referencing worker source URLs
    re.compile(r"^(runCycle|onmessage)\s*@\s*data:text/javascript;base64,"),
    # Redundant engine line (keep 'received:' / 'render done', drop 'received eventType:')
    re.compile(r"\[ReactEngine\] received eventType:"),
    # Redundant worker event receipt — always says nextRunCycle or Object;
    # the actual payload appears in the subsequent unwrap/runCycle lines
    re.compile(r"\[ProcessingWorker\] Received event:"),
    # Dev warnings
    re.compile(r"Download the React DevTools"),
    re.compile(r"Invalid DOM property"),
    re.compile(r"^\$p\s*@"),
    # Viewport resize noise
    re.compile(r"\[Viewport\] push update event"),
]

# JS/TS file prefixes to strip. These vary per build and add noise without
# information (the tagged content like [ReactEngine] already identifies the
# source). Matches patterns like:
#   index-BJzk0a9c.js:420        (minified, v1)
#   py_worker.js:35              (production worker)
#   d3i_py_worker.js:6           (v2 worker)
#   engine.tsx:21                (dev mode, unminified)
#   fake_bridge.ts:52            (dev mode)
#   app-81b0087...js?vsn=d:52   (Phoenix/Elixir asset)
#   pyodide.asm.js:9             (Pyodide runtime)
#   (index):1                    (inline script)
#   react-dom-client.development.js:24871
JS_PREFIX_RE = re.compile(
    r"^(?:"
    r"\(index\):\d+\s*"                                  # Chrome inline script
    r"|[\w._-]+\.(?:js|ts|tsx)(?:\?[^:]+)?:\d+\s*"      # any .js/.ts/.tsx file:line
    r"|pyodide\.asm\.js:\d+\s*"                          # pyodide runtime
    r")"
)

# Max chars for a line before truncation kicks in
MAX_LINE_LEN = 300


def is_noise(line: str) -> bool:
    """Check if a line is noise that should be stripped entirely."""
    stripped = line.strip()
    if not stripped:
        return True
    for pat in NOISE_PATTERNS:
        if pat.search(stripped):
            return True
    return False


def strip_js_prefix(line: str) -> str:
    """Remove JS file:line prefixes that vary per build."""
    return JS_PREFIX_RE.sub("", line)


def truncate_line(line: str) -> str:
    """Truncate long lines, preserving the meaningful prefix."""
    if len(line) <= MAX_LINE_LEN:
        return line

    # Try to find where a JSON payload starts (past the log prefix)
    for i, c in enumerate(line):
        if c in "{[" and i > 20:
            prefix = line[:i]
            payload = line[i:]
            # Extract __type__ if present for context
            m = re.search(r"__type__[\"']?\s*[:=]\s*[\"']?(\w+)", payload)
            type_hint = f" ({m.group(1)})" if m else ""
            budget = MAX_LINE_LEN - len(prefix)
            return f"{prefix}{payload[:budget]}...{type_hint} [{len(payload):,} chars]"

    return line[:MAX_LINE_LEN] + f"... [{len(line):,} chars]"


def collapse_void_cycles(lines):
    """Collapse consecutive PayloadVoid run cycles into a single summary.

    In the D3I workflow, a "void cycle" is when the host sends nextRunCycle
    with a PayloadVoid response (e.g., user clicked continue, or a system
    command was acknowledged). Three log lines per cycle get collapsed into
    one summary line.
    """
    result = []
    void_count = 0
    void_start_lineno = None

    for lineno, text in lines:
        is_void = "PayloadVoid" in text and "[ProcessingWorker]" in text
        if is_void:
            if void_count == 0:
                void_start_lineno = lineno
            void_count += 1
            continue

        # Flush accumulated void cycles
        if void_count > 0:
            if void_count <= 2:
                result.append(
                    (void_start_lineno, f"--- {void_count} PayloadVoid cycle(s) ---")
                )
            else:
                result.append(
                    (
                        void_start_lineno,
                        f"--- {void_count} PayloadVoid cycles (continue/ack) ---",
                    )
                )
            void_count = 0
            void_start_lineno = None

        result.append((lineno, text))

    # Flush any remaining
    if void_count > 0:
        label = "cycle" if void_count == 1 else "cycles"
        result.append(
            (void_start_lineno, f"--- {void_count} PayloadVoid {label} ---")
        )

    return result


def detect_metadata(raw_lines):
    """Extract session metadata from the raw log lines."""
    meta = {
        "mode": "unknown",
        "port": None,
        "platforms": set(),
        "errors": [],
        "timestamps": [],
    }

    for line in raw_lines:
        # Bridge mode
        if "fake bridge" in line.lower() or "[FakeBridge]" in line:
            meta["mode"] = "FakeBridge (local/GitHub Pages)"
        elif "[LiveBridge]" in line:
            meta["mode"] = "LiveBridge (deployed)"

        # Python port name (e.g., port.general_ddp_analyzer)
        m = re.search(r"--- (port\.\w+) ---", line)
        if m and not meta["port"]:
            meta["port"] = m.group(1)

        # Platforms from CommandSystemLog messages or Python log lines.
        # These appear as [PlatformName] in log messages. Exclude system tags.
        SYSTEM_TAGS = {"LiveBridge", "FakeBridge", "Feldspar", "ReactEngine",
                       "WorkerProcessingEngine", "ProcessingWorker",
                       "CommandRouter", "Viewport", "Intervention"}
        for m in re.finditer(r"\[(\w+)\] (?:Consent|Donation|Extraction|File received|Validation|Starting)", line):
            tag = m.group(1)
            if tag not in SYSTEM_TAGS:
                meta["platforms"].add(tag)
        # Also catch "Starting platform: X"
        m = re.search(r"Starting platform:\s*(\w+)", line)
        if m:
            meta["platforms"].add(m.group(1))

        # Timestamps from Python log lines
        m = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", line)
        if m:
            meta["timestamps"].append(m.group())

        # Errors (be selective — skip DevTools/DOM noise)
        if "ERROR" in line and "DevTools" not in line:
            meta["errors"].append(line.strip()[:200])
        elif "PropsUIPageError" in line:
            meta["errors"].append(line.strip()[:200])

    return meta


def clean_log(filepath, save=False):
    """Clean a D3I dev console log file.

    Returns the cleaned output as a string.
    If save=True, also writes to <filepath>.cleaned.log
    """
    path = Path(filepath)
    if not path.exists():
        print(f"Error: {filepath} not found", file=sys.stderr)
        sys.exit(1)

    raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    total_chars = sum(len(l) for l in raw_lines)

    # Phase 1: Filter noise lines
    signal = []
    noise_count = 0
    for i, line in enumerate(raw_lines, 1):
        if is_noise(line):
            noise_count += 1
            continue
        cleaned = strip_js_prefix(line.strip())
        cleaned = truncate_line(cleaned)
        signal.append((i, cleaned))

    # Phase 2: Collapse consecutive PayloadVoid cycles
    signal = collapse_void_cycles(signal)

    # Phase 3: Extract metadata
    meta = detect_metadata(raw_lines)

    # Build output
    cleaned_chars = sum(len(text) for _, text in signal)
    reduction = (
        (1 - cleaned_chars / total_chars) * 100 if total_chars > 0 else 0
    )

    header = [
        f"=== D3I Dev Console Log: {path.name} ===",
        f"Original: {len(raw_lines)} lines, {total_chars:,} chars",
        f"Cleaned:  {len(signal)} signal lines ({noise_count} noise lines stripped, {reduction:.0f}% reduction)",
        f"Mode:     {meta['mode']}",
    ]
    if meta["port"]:
        header.append(f"Port:     {meta['port']}")
    if meta["platforms"]:
        header.append(f"Platforms: {', '.join(sorted(meta['platforms']))}")
    if meta["timestamps"]:
        unique_ts = list(dict.fromkeys(meta["timestamps"]))  # dedupe, preserve order
        header.append(f"Time:     {unique_ts[0]}" + (f" -> {unique_ts[-1]}" if len(unique_ts) > 1 else ""))
    if meta["errors"]:
        header.append(f"Errors:   {len(meta['errors'])} detected")
        for e in meta["errors"][:5]:
            header.append(f"  ! {e}")
    header.extend(["=" * 50, ""])

    body = [f"{lineno:>5}| {text}" for lineno, text in signal]
    result = "\n".join(header + body)

    if save:
        out_path = path.with_suffix(".cleaned.log")
        out_path.write_text(result, encoding="utf-8")
        result += f"\n\n[Saved to {out_path}]"

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Clean D3I browser dev console logs for efficient analysis"
    )
    parser.add_argument("logfile", help="Path to the .log file")
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save cleaned output alongside original as .cleaned.log",
    )
    args = parser.parse_args()

    print(clean_log(args.logfile, save=args.save))


if __name__ == "__main__":
    main()
