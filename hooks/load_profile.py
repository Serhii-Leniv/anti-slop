#!/usr/bin/env python3
"""
SessionStart hook.
Checks if personal profile exists. If not, hints to run /no-slop init.
If exists, prints summary (goes to session context).
"""

import sys
import json
import os

PROFILE_PATH = os.path.expanduser("~/.claude/anti-slop-profile.json")


def main():
    if not os.path.exists(PROFILE_PATH):
        # first time — nudge user, don't block
        print(
            "[anti-slop] No personal profile found. "
            "Run /no-slop init to scan your codebase and personalize rules. "
            "Using default rules for now.",
            file=sys.stderr,
        )
        sys.exit(0)

    try:
        with open(PROFILE_PATH) as f:
            profile = json.load(f)
    except Exception:
        sys.exit(0)

    allowlisted = profile.get("allowlist_rules", [])
    if allowlisted:
        print(
            f"[anti-slop] Profile loaded. {len(allowlisted)} rule(s) allowlisted for this project.",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
