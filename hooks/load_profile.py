#!/usr/bin/env python3
"""
SessionStart hook.
Checks if personal profile exists. If not, hints to run /no-slop init.
If exists, prints summary (goes to session context).
"""

import sys
import json
import os

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(HOOK_DIR)
SCANNER_DIR = os.path.join(PLUGIN_DIR, "scanner")
sys.path.insert(0, SCANNER_DIR)

from detect import resolve_profile_path


def main():
    profile_path = resolve_profile_path()

    if not os.path.exists(profile_path):
        # first time — nudge user, don't block
        print(
            "[anti-slop] No profile found. "
            "Run /no-slop init to scan your codebase and personalize rules "
            "(saves to project root as .anti-slop-profile.json). "
            "Using default rules for now.",
            file=sys.stderr,
        )
        sys.exit(0)

    try:
        with open(profile_path) as f:
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
