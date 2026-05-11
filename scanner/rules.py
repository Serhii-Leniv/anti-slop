"""
Slop detection rules. Pure regex + AST. Zero LLM calls.
Each rule: { id, pattern, message, severity (1-3), file_types }
severity: 1=minor, 2=real slop, 3=rebuild
"""

import re

CODE_RULES = [
    # --- Exception handling ---
    {
        "id": "swallowed_exception",
        "pattern": r"catch\s*\(\s*\w+\s*\)\s*\{\s*\}",
        "message": "swallowed exception — hides errors silently",
        "severity": 3,
        "file_types": [".ts", ".tsx", ".js", ".jsx", ".java", ".cs"],
    },
    {
        "id": "bare_except",
        "pattern": r"except\s*:",
        "message": "bare except: — catches everything including KeyboardInterrupt",
        "severity": 3,
        "file_types": [".py"],
    },
    {
        "id": "pass_in_except",
        "pattern": r"except[^:]*:\s*\n\s*pass\b",
        "message": "pass in except — error silently ignored",
        "severity": 3,
        "file_types": [".py"],
        "multiline": True,
    },

    # --- Generic names ---
    {
        "id": "generic_var_data",
        "pattern": r"\bconst\s+data\s*=|\blet\s+data\s*=|\bvar\s+data\s*=",
        "message": "generic name 'data' — name what it actually contains",
        "severity": 2,
        "file_types": [".ts", ".tsx", ".js", ".jsx"],
    },
    {
        "id": "generic_var_result",
        "pattern": r"\bconst\s+result\s*=|\blet\s+result\s*=",
        "message": "generic name 'result' — name what it actually is",
        "severity": 1,
        "file_types": [".ts", ".tsx", ".js", ".jsx", ".py"],
    },
    {
        "id": "generic_handler",
        "pattern": r"\bfunction\s+handleClick\b|\bconst\s+handleClick\s*=",
        "message": "generic handler name 'handleClick' — name what it handles",
        "severity": 1,
        "file_types": [".ts", ".tsx", ".js", ".jsx"],
    },

    # --- Console/print in production ---
    {
        "id": "console_log",
        "pattern": r"\bconsole\.log\(",
        "message": "console.log in production path — use structured logger",
        "severity": 2,
        "file_types": [".ts", ".tsx", ".js", ".jsx"],
        "skip_in_tests": True,
    },
    {
        "id": "print_debug",
        "pattern": r"^\s*print\(",
        "message": "print() debug statement — use logging module",
        "severity": 2,
        "file_types": [".py"],
        "skip_in_tests": True,
    },

    # --- TypeScript any ---
    {
        "id": "ts_any",
        "pattern": r":\s*any\b",
        "message": "TypeScript 'any' — defeats type safety, name the actual type",
        "severity": 2,
        "file_types": [".ts", ".tsx"],
    },

    # --- Obvious comments ---
    {
        "id": "obvious_comment_js",
        "pattern": r"//\s*(This function|This method|This component|Here we|We need to|Now we)\b",
        "message": "obvious comment — explains what code does, not why",
        "severity": 1,
        "file_types": [".ts", ".tsx", ".js", ".jsx", ".go"],
    },
    {
        "id": "obvious_comment_py",
        "pattern": r"#\s*(This function|This method|This component|Here we|We need to|Now we)\b",
        "message": "obvious comment — explains what code does, not why",
        "severity": 1,
        "file_types": [".py"],
    },

    # --- TODO without ticket ---
    {
        "id": "todo_no_ticket_js",
        "pattern": r"//\s*TODO(?!\s*[:#\(]\s*[A-Z]+-\d+|\s*\()",
        "message": "TODO without ticket reference — will never get done",
        "severity": 1,
        "file_types": [".ts", ".tsx", ".js", ".jsx", ".go"],
    },
    {
        "id": "todo_no_ticket_py",
        "pattern": r"#\s*TODO(?!\s*[:#\(]\s*[A-Z]+-\d+|\s*\()",
        "message": "TODO without ticket reference — will never get done",
        "severity": 1,
        "file_types": [".py"],
    },

    # --- Magic numbers ---
    {
        "id": "magic_number",
        "pattern": r"(?<!['\"\w])\b(?!0\b|1\b|2\b|100\b)\d{3,}\b(?!['\"\w])",
        "message": "magic number — extract to named constant",
        "severity": 1,
        "file_types": [".ts", ".tsx", ".js", ".jsx", ".py"],
    },

    # --- No timeout on fetch ---
    {
        "id": "fetch_no_timeout",
        "pattern": r"\bfetch\s*\(",
        "message": "fetch() with no timeout — hangs forever on network failure",
        "severity": 2,
        "file_types": [".ts", ".tsx", ".js", ".jsx"],
    },
]

UI_RULES = [
    # --- Fonts ---
    {
        "id": "inter_font",
        "pattern": r"['\"]Inter['\"]|font-family:\s*Inter|fontFamily:\s*['\"]Inter",
        "message": "Inter font — AI default, no design intent. Pick deliberately.",
        "severity": 2,
        "file_types": [".tsx", ".jsx", ".css", ".scss"],
    },

    # --- Colors ---
    {
        "id": "purple_gradient",
        "pattern": r"#7[Cc]3[Aa][Ee][Dd]|#8[Bb]5[Cc][Ff]6|from-purple|to-purple|via-purple",
        "message": "purple gradient — AI default UI. Pick a color with intent.",
        "severity": 2,
        "file_types": [".tsx", ".jsx", ".css", ".scss"],
    },

    # --- Tailwind slop ---
    {
        "id": "rounded_full_generic",
        "pattern": r"rounded-full",
        "message": "rounded-full on non-pill/avatar — usually unintentional full circle",
        "severity": 1,
        "file_types": [".tsx", ".jsx"],
    },
    {
        "id": "shadow_lg_everywhere",
        "pattern": r"shadow-lg",
        "message": "shadow-lg as default — overused, flattens visual hierarchy",
        "severity": 1,
        "file_types": [".tsx", ".jsx"],
    },
    {
        "id": "hover_opacity",
        "pattern": r"hover:opacity-\d+",
        "message": "hover:opacity as default interaction — no design intent",
        "severity": 1,
        "file_types": [".tsx", ".jsx"],
    },

    # --- Placeholders ---
    {
        "id": "john_doe_placeholder",
        "pattern": r"John Doe|Jane Doe|john\.doe@|janedoe",
        "message": "John/Jane Doe placeholder — use realistic domain-specific data",
        "severity": 1,
        "file_types": [".tsx", ".jsx"],
    },
    {
        "id": "lorem_ipsum",
        "pattern": r"[Ll]orem ipsum",
        "message": "Lorem ipsum — use real content or realistic placeholder",
        "severity": 2,
        "file_types": [".tsx", ".jsx", ".html"],
    },

    # --- 3-column card grid ---
    {
        "id": "three_col_grid",
        "pattern": r"grid-cols-3|grid-template-columns:\s*repeat\(3",
        "message": "3-column card grid — AI default layout, intentional?",
        "severity": 1,
        "file_types": [".tsx", ".jsx", ".css"],
    },
]

PROSE_RULES = [
    # --- Throat-clearing openers ---
    {
        "id": "certainly",
        "pattern": r"(?i)^certainly[!,\s]|^of course[!,\s]|^absolutely[!,\s]|^great question",
        "message": "AI throat-clearing opener — cut it",
        "severity": 3,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "let_me",
        "pattern": r"(?i)\blet me (break|walk|explain|show|help)",
        "message": "'Let me...' — AI tell, just do it",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },

    # --- Banned words ---
    {
        "id": "delve",
        "pattern": r"(?i)\bdelve\b",
        "message": "'delve' — top AI word, use 'explore'/'examine'/'look at'",
        "severity": 3,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "leverage",
        "pattern": r"(?i)\bleverage\b",
        "message": "'leverage' — corporate AI slop, use 'use'",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "utilize",
        "pattern": r"(?i)\butilize\b",
        "message": "'utilize' — use 'use'",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "it_is_worth_noting",
        "pattern": r"(?i)it('s| is) worth noting",
        "message": "'it's worth noting' — AI hedge, just say it",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "in_conclusion",
        "pattern": r"(?i)^in conclusion[,\s]|^in summary[,\s]|^to summarize[,\s]",
        "message": "summary opener — AI closer, cut or rewrite",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },

    # --- Structural slop ---
    {
        "id": "not_because_because",
        "pattern": r"(?i)not because.*\.\s+because",
        "message": "'Not because X. Because Y.' — AI dramatic structure",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
]


def get_rules_for_file(filepath: str, is_test: bool = False) -> list:
    """Return applicable rules for a given file path."""
    import os
    ext = os.path.splitext(filepath)[1].lower()

    applicable = []
    all_rules = CODE_RULES + UI_RULES + PROSE_RULES

    for rule in all_rules:
        if ext not in rule.get("file_types", []):
            continue
        if is_test and rule.get("skip_in_tests", False):
            continue
        applicable.append(rule)

    return applicable
