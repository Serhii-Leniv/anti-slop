"""
Core scanner. Reads file, runs rules, returns findings.
No LLM. No network. Pure local.
"""

import re
import os
import json
from rules import get_rules_for_file


SEVERITY_LABELS = {1: "minor", 2: "slop", 3: "rebuild"}

THRESHOLD = 2  # only report to Claude if max severity >= this


def find_project_root(start_path: str):
    """Walk up from start_path looking for project root markers. Returns path or None."""
    markers = {".git", "package.json", "pyproject.toml", "Cargo.toml", "go.mod"}
    current = os.path.abspath(start_path)
    while True:
        for marker in markers:
            if os.path.exists(os.path.join(current, marker)):
                return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def resolve_profile_path(filepath: str = None) -> str:
    """Return project-local profile if it exists, else global ~/.claude/ fallback."""
    global_path = os.path.expanduser("~/.claude/anti-slop-profile.json")
    start = os.path.dirname(os.path.abspath(filepath)) if filepath else os.getcwd()
    root = find_project_root(start)
    if root:
        local_path = os.path.join(root, ".anti-slop-profile.json")
        if os.path.exists(local_path):
            return local_path
    return global_path


def is_test_file(filepath: str) -> bool:
    name = os.path.basename(filepath).lower()
    return any(x in name for x in [".test.", ".spec.", "_test.", "test_", "__test__"])


def load_profile(profile_path: str) -> dict:
    """Load personal allowlist. If not found, return empty."""
    if os.path.exists(profile_path):
        with open(profile_path) as f:
            return json.load(f)
    return {"allowlist_rules": [], "allowlist_patterns": []}


def scan_file(filepath: str, profile: dict) -> list:
    """
    Scan one file. Returns list of findings:
    [{ line, rule_id, message, severity }]
    """
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return []

    lines = content.splitlines(keepends=True)
    is_test = is_test_file(filepath)
    rules = get_rules_for_file(filepath, is_test)
    allowlisted = set(profile.get("allowlist_rules", []))

    findings = []

    for rule in rules:
        if rule["id"] in allowlisted:
            continue

        if rule.get("multiline"):
            # scan full content — pattern spans multiple lines
            pattern = re.compile(rule["pattern"], re.MULTILINE | re.DOTALL)
            for match in pattern.finditer(content):
                lineno = content[:match.start()].count("\n") + 1
                snippet = lines[lineno - 1].rstrip() if lineno <= len(lines) else ""
                findings.append({
                    "line": lineno,
                    "rule_id": rule["id"],
                    "message": rule["message"],
                    "severity": rule["severity"],
                    "severity_label": SEVERITY_LABELS[rule["severity"]],
                    "snippet": snippet,
                })
        else:
            pattern = re.compile(rule["pattern"], re.MULTILINE)
            for lineno, line in enumerate(lines, start=1):
                if pattern.search(line):
                    findings.append({
                        "line": lineno,
                        "rule_id": rule["id"],
                        "message": rule["message"],
                        "severity": rule["severity"],
                        "severity_label": SEVERITY_LABELS[rule["severity"]],
                        "snippet": line.rstrip(),
                    })

    # deduplicate same rule hitting same line
    seen = set()
    unique = []
    for f in findings:
        key = (f["line"], f["rule_id"])
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def format_report(filepath: str, findings: list) -> str:
    """
    Compact report injected into Claude context via stderr.
    ~80-200 tokens. Points at lines, doesn't explain the whole file.
    """
    if not findings:
        return ""

    max_sev = max(f["severity"] for f in findings)
    if max_sev < THRESHOLD:
        return ""  # below threshold, log silently, don't bother Claude

    rel_path = os.path.relpath(filepath)
    lines = [f"[anti-slop] {len(findings)} finding(s) in {rel_path}:"]

    # sort by severity desc, then line
    for f in sorted(findings, key=lambda x: (-x["severity"], x["line"])):
        label = f["severity_label"].upper()
        lines.append(f"  L{f['line']}: [{label}] {f['message']}")

    lines.append("Fix before continuing.")
    return "\n".join(lines)


def log_silently(filepath: str, findings: list, log_path: str):
    """Append minor findings to log without bothering Claude."""
    if not findings:
        return
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        for finding in findings:
            f.write(json.dumps({
                "file": filepath,
                **finding
            }) + "\n")
