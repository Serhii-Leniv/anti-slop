"""
Scans existing codebase to build a personal slop profile.
Detects patterns you already use legitimately so we don't flag them.
Zero LLM. Pure AST/regex. Runs once.
"""

import os
import re
import json
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from detect import find_project_root

# Rules that might be legit depending on project
CONTEXTUAL_RULES = {
    "inter_font": {
        "check": lambda content: bool(re.search(r"['\"]Inter['\"]", content)),
        "threshold": 3,
        "reason": "Inter font used 3+ times — likely your design system",
    },
    "console_log": {
        "check": lambda content: bool(re.search(r"console\.log\(", content)),
        "threshold": 5,
        "reason": "console.log used frequently — may be intentional debug tooling",
    },
    "ts_any": {
        "check": lambda content: bool(re.search(r":\s*any\b", content)),
        "threshold": 10,
        "reason": "TypeScript 'any' used heavily — may be legacy/migration codebase",
    },
    "three_col_grid": {
        "check": lambda content: bool(re.search(r"grid-cols-3", content)),
        "threshold": 2,
        "reason": "3-column grid used multiple times — may be intentional layout",
    },
    "fetch_no_timeout": {
        "check": lambda content: bool(re.search(r"\bfetch\s*\(", content)),
        "threshold": 3,
        "reason": "fetch() used frequently — project may have wrapper with timeout built in",
    },
    "generic_var_result": {
        "check": lambda content: bool(re.search(r"\bconst\s+result\s*=|\blet\s+result\s*=", content)),
        "threshold": 5,
        "reason": "'result' used frequently — may be intentional convention in this codebase",
    },
    "unhandled_promise": {
        "check": lambda content: bool(re.search(r"\.then\s*\(", content)),
        "threshold": 8,
        "reason": ".then() chains common — project may use promise patterns throughout",
    },
    "shadow_lg_everywhere": {
        "check": lambda content: bool(re.search(r"shadow-lg", content)),
        "threshold": 5,
        "reason": "shadow-lg used frequently — may be your design system default",
    },
}


def scan_project(root: str, max_files: int = 200) -> dict:
    """
    Walk project, count pattern occurrences across files.
    Returns allowlist of rules to skip for this project.
    """
    counters = Counter()
    scanned = 0

    extensions = {".ts", ".tsx", ".js", ".jsx", ".py", ".css", ".scss", ".go"}

    for dirpath, dirnames, filenames in os.walk(root):
        # skip common non-source dirs
        dirnames[:] = [
            d for d in dirnames
            if d not in {"node_modules", ".git", "dist", "build", ".next", "__pycache__", "venv", ".venv"}
        ]

        for filename in filenames:
            if scanned >= max_files:
                break
            ext = os.path.splitext(filename)[1].lower()
            if ext not in extensions:
                continue

            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            for rule_id, config in CONTEXTUAL_RULES.items():
                if config["check"](content):
                    counters[rule_id] += 1

            scanned += 1

    allowlist = []
    reasons = {}

    for rule_id, config in CONTEXTUAL_RULES.items():
        count = counters.get(rule_id, 0)
        if count >= config["threshold"]:
            allowlist.append(rule_id)
            reasons[rule_id] = config["reason"]

    return {
        "allowlist_rules": allowlist,
        "allowlist_reasons": reasons,
        "scanned_files": scanned,
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    profile = scan_project(root)

    project_root = find_project_root(os.path.abspath(root))
    if project_root:
        output_path = os.path.join(project_root, ".anti-slop-profile.json")
    else:
        output_path = os.path.expanduser("~/.claude/anti-slop-profile.json")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"Profile built from {profile['scanned_files']} files.")
    print(f"Allowlisted {len(profile['allowlist_rules'])} rules: {profile['allowlist_rules']}")
    print(f"Saved to {output_path}")
