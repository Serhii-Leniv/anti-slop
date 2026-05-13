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

    # --- Magic numbers (excludes common HTTP codes, ports, time values, powers of 2) ---
    {
        "id": "magic_number",
        "pattern": r"(?<!['\"\w])\b(?!0\b|1\b|2\b|3\b|4\b|5\b|10\b|16\b|32\b|64\b|100\b|128\b|200\b|201\b|204\b|256\b|300\b|301\b|302\b|304\b|307\b|308\b|400\b|401\b|403\b|404\b|408\b|409\b|410\b|422\b|429\b|500\b|501\b|502\b|503\b|504\b|1000\b|1024\b|2048\b|3000\b|3600\b|4096\b|5000\b|8000\b|8080\b|8443\b|9000\b|60000\b|86400\b)\d{3,}\b(?!['\"\w%])",
        "message": "magic number — extract to named constant",
        "severity": 1,
        "file_types": [".ts", ".tsx", ".js", ".jsx", ".py"],
    },

    # --- No timeout on fetch ---
    # severity 1 (silent log): line-by-line regex can't see multiline fetch({signal})
    {
        "id": "fetch_no_timeout",
        "pattern": r"\bfetch\s*\((?![^)]*\b(signal|AbortSignal|AbortController|timeout)\b)",
        "message": "fetch() with no timeout — hangs forever on network failure",
        "severity": 1,
        "file_types": [".ts", ".tsx", ".js", ".jsx"],
    },

    # --- Unhandled promise ---
    # severity 2: can't detect .catch() elsewhere in a chain without AST
    {
        "id": "unhandled_promise",
        "pattern": r"\.then\s*\([^)]+\)\s*;",
        "message": "unhandled promise — .then() with no .catch(), rejection silently lost",
        "severity": 2,
        "file_types": [".ts", ".tsx", ".js", ".jsx"],
    },

    # --- .catch swallows error ---
    {
        "id": "catch_console_error",
        "pattern": r"\.catch\s*\(\s*console\.(error|log|warn)\s*\)",
        "message": ".catch(console.error) — logs then swallows, caller never knows it failed",
        "severity": 2,
        "file_types": [".ts", ".tsx", ".js", ".jsx"],
    },

    # --- Hardcoded secrets ---
    {
        "id": "hardcoded_secret",
        "pattern": r"(?i)(password|secret|api_key|apikey|token|auth_token)\s*=\s*['\"][^'\"]{4,}['\"]",
        "message": "hardcoded secret — move to env var",
        "severity": 3,
        "file_types": [".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".java", ".cs"],
    },

    # async_no_trycatch removed: regex lookahead [^}]* stops at first } in body
    # (object literal, generic type, destructure), so virtually every real async
    # function fires. Needs AST — use @typescript-eslint/no-floating-promises instead.

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

    # --- Arbitrary z-index ---
    {
        "id": "z_index_arbitrary",
        "pattern": r"z-index:\s*(999|9999|99999)|z-\[999\]|z-\[9999\]",
        "message": "arbitrary z-index — use design system z-index scale",
        "severity": 2,
        "file_types": [".tsx", ".jsx", ".css", ".scss"],
    },

    # --- !important ---
    {
        "id": "css_important",
        "pattern": r"!important",
        "message": "!important — specificity hack, fix the selector instead",
        "severity": 2,
        "file_types": [".css", ".scss", ".tsx", ".jsx"],
    },

    # --- Missing aria on interactive elements ---
    {
        "id": "div_onclick_no_aria",
        # Two lookaheads from <div: must have onClick, must NOT have aria- anywhere before >
        "pattern": r"<div\b(?=[^>]*\bonClick\b)(?![^>]*\baria-)[^>]*>",
        "message": "div with onClick but no aria role — use <button> or add role+aria",
        "severity": 2,
        "file_types": [".tsx", ".jsx"],
    },

    # --- Roboto (same AI default as Inter) ---
    {
        "id": "roboto_font",
        "pattern": r"['\"]Roboto['\"]|font-family:\s*Roboto|fontFamily:\s*['\"]Roboto",
        "message": "Roboto font — AI default, no design intent. Pick deliberately.",
        "severity": 2,
        "file_types": [".tsx", ".jsx", ".css", ".scss"],
    },

    # --- Blue gradient (second most common AI color) ---
    {
        "id": "blue_gradient_generic",
        "pattern": r"from-blue-500 to-purple|from-indigo.*to-purple|bg-gradient.*blue.*purple",
        "message": "blue-to-purple gradient — AI signature combo, pick with intent",
        "severity": 2,
        "file_types": [".tsx", ".jsx"],
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

    # --- High-frequency AI words (research-verified) ---
    {
        "id": "tapestry",
        "pattern": r"(?i)\btapestry\b",
        "message": "'tapestry' — 35x more common in AI text, spatial metaphor filler",
        "severity": 3,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "multifaceted",
        "pattern": r"(?i)\bmultifaceted\b",
        "message": "'multifaceted' — 28x more common in AI text, use 'complex' or be specific",
        "severity": 3,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "furthermore_moreover",
        "pattern": r"(?i)\b(furthermore|moreover)\b",
        "message": "'furthermore/moreover' — AI transition filler, cut or rewrite",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "needless_to_say",
        "pattern": r"(?i)needless to say",
        "message": "'needless to say' — then don't say it",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "paradigm_shift",
        "pattern": r"(?i)paradigm[\s-]shift",
        "message": "'paradigm shift' — overused buzzword, describe the actual change",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "seamless",
        "pattern": r"(?i)\bseamless(ly)?\b",
        "message": "'seamless' — meaningless AI adjective, describe what actually happens",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "robust",
        "pattern": r"(?i)\brobust\b",
        "message": "'robust' — vague AI praise word, say what specifically makes it reliable",
        "severity": 1,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "cutting_edge",
        "pattern": r"(?i)cutting[\s-]edge",
        "message": "'cutting-edge' — marketing slop, describe the actual capability",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "at_its_core",
        "pattern": r"(?i)at its core",
        "message": "'at its core' — AI filler phrase, just say the thing",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "lets_unpack",
        "pattern": r"(?i)let'?s unpack",
        "message": "'let's unpack' — AI tell, just explain it",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "speaks_volumes",
        "pattern": r"(?i)speaks volumes",
        "message": "'speaks volumes' — cliché, say what it actually means",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "game_changer",
        "pattern": r"(?i)game[\s-]changer",
        "message": "'game-changer' — marketing filler, describe the actual impact",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "synergy",
        "pattern": r"(?i)\bsynergy\b|\bsynergies\b",
        "message": "'synergy' — corporate AI buzzword",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "pivotal",
        "pattern": r"(?i)\bpivotal\b",
        "message": "'pivotal' — AI intensifier, use 'key' or 'critical' or just drop it",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "nuanced",
        "pattern": r"(?i)\bnuanced\b",
        "message": "'nuanced' — vague, describe the actual complexity",
        "severity": 1,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "compelling",
        "pattern": r"(?i)\bcompelling\b",
        "message": "'compelling' — AI praise word, show why it's compelling instead",
        "severity": 1,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "indeed",
        "pattern": r"(?i)^indeed[,\s]|\. indeed[,\s]",
        "message": "'Indeed' as sentence opener — AI verbal tic, cut it",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "testament",
        "pattern": r"(?i)\ba testament to\b",
        "message": "'a testament to' — AI filler, say what it shows directly",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "navigate_landscape",
        "pattern": r"(?i)navigate (the |this |a )?(complex |digital |ever-changing )?landscape",
        "message": "'navigate the landscape' — AI spatial metaphor, be specific",
        "severity": 2,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "todays_world",
        "pattern": r"(?i)in today'?s (fast-paced|digital|modern|ever-changing) (world|age|landscape|era)",
        "message": "'in today's fast-paced world' — AI generic opener, cut entirely",
        "severity": 3,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "comprehensive",
        "pattern": r"(?i)\bcomprehensive\b",
        "message": "'comprehensive' — vague AI intensifier, just describe what it covers",
        "severity": 1,
        "file_types": [".md", ".txt"],
    },
    {
        "id": "crucial",
        "pattern": r"(?i)\bcrucial\b",
        "message": "'crucial' — overused AI intensifier, say why it matters",
        "severity": 1,
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
