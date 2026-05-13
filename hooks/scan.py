#!/usr/bin/env python3
"""
PostToolUse hook for Write|Edit events.
Works with Claude Code, Cursor, and Antigravity.
Reads stdin JSON, extracts file path, runs scanner.
Exits 0 always — never blocks writes, just injects findings via stderr.
Minor findings go to log silently.
"""

import sys
import json
import os

# resolve scanner path — works regardless of platform or install location
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(HOOK_DIR)
SCANNER_DIR = os.path.join(PLUGIN_DIR, "scanner")
sys.path.insert(0, SCANNER_DIR)

from detect import scan_file, format_report, log_silently, load_profile, resolve_profile_path, THRESHOLD

LOG_PATH = os.path.expanduser("~/.claude/anti-slop-log.jsonl")


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # extract file path depending on tool
    if tool_name == "Write":
        filepath = tool_input.get("file_path", "")
    elif tool_name == "Edit":
        filepath = tool_input.get("file_path", "")
    else:
        sys.exit(0)

    if not filepath:
        sys.exit(0)

    filepath = os.path.expanduser(filepath)
    profile = load_profile(resolve_profile_path(filepath))
    findings = scan_file(filepath, profile)

    if not findings:
        sys.exit(0)

    # separate by threshold
    above = [f for f in findings if f["severity"] >= THRESHOLD]
    below = [f for f in findings if f["severity"] < THRESHOLD]

    # minor findings: silent log
    if below:
        log_silently(filepath, below, LOG_PATH)

    # real findings: tell Claude
    if above:
        report = format_report(filepath, above)
        if report:
            print(report, file=sys.stderr)

    sys.exit(0)  # never block the write


if __name__ == "__main__":
    main()
