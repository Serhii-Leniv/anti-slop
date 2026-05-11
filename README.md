![license](https://img.shields.io/github/license/Serhii-Leniv/anti-slop) ![stars](https://img.shields.io/github/stars/Serhii-Leniv/anti-slop?style=flat) ![issues](https://img.shields.io/github/issues/Serhii-Leniv/anti-slop) ![python](https://img.shields.io/badge/python-3.8%2B-blue) ![platforms](https://img.shields.io/badge/works%20on-Claude%20Code%20%7C%20Cursor%20%7C%20Antigravity-black)

<div align="center">
<pre>
              _   _            _             
             | | (_)          | |            
   __ _ _ __ | |  _ ______ ___| | ___  _ __  
  / _` | '_ \| __| |______/ __| |/ _ \| '_ \ 
 | (_| | | | | |_| |      \__ \ | (_) | |_) |
  \__,_|_| |_|\__|_|      |___/_|\___/| .__/ 
                                      | |    
                                      |_|    
</pre>
</div>

> Stop AI from shipping AI-looking code.

AI coding agents write fast. They also write the same patterns every time — swallowed exceptions, generic variable names, Inter font, purple gradients, "delve into", "it's worth noting". It works. It just looks and feels like it came from a machine.

**anti-slop** fires on every file you write and catches it before it lands in your codebase.

---

## The Problem

Every AI coding session produces some version of this:

```ts
// ❌ what Claude ships by default
const data = await fetch('/api/users');
try {
  const result = data.json();
  console.log(result);
} catch(e) {}
```

```tsx
// ❌ every AI frontend looks identical
<div className="font-inter bg-gradient-to-r from-purple-500 shadow-lg rounded-full hover:opacity-80">
  <h1>Welcome, John Doe</h1>
</div>
```

```md
<!-- ❌ every AI doc sounds the same -->
Certainly! It's worth noting that we can leverage this to delve into...
In conclusion, this approach utilizes best practices.
```

It runs. It deploys. It works. But it's recognizably, unmistakably AI slop.

---

## The Solution

anti-slop installs as a plugin and watches every file Claude writes. The moment slop is detected, it tells Claude exactly what's wrong and where — before moving on.

```
Claude writes auth.ts
  → scanner fires locally (0 tokens, pure regex/AST)
  → finds 3 issues
  → sends to Claude: "L45 swallowed exception, L12 generic name, L78 console.log"
  → Claude fixes inline using existing context
  → no extra LLM call needed
```

Zero friction. You never have to ask for a review. It just happens.

---

## Why anti-slop

- **Automatic** — fires on every file write, no invocation needed
- **Multi-domain** — code, UI, and prose in one plugin
- **Zero detection cost** — pure local regex/AST, no LLM until something is found
- **Adapts to your codebase** — `/no-slop init` learns your patterns, stops false positives
- **Multi-platform** — Claude Code, Cursor, Google Antigravity

---

## What It Catches

### Code
| Pattern | Severity |
|---|---|
| `catch(e) {}` — swallowed exception | 🔴 REBUILD |
| `except:` / `except SomeError: pass` | 🔴 REBUILD |
| Hardcoded secrets (`password = "..."`) | 🔴 REBUILD |
| `.then()` with no `.catch()` | 🔴 REBUILD |
| `const data =`, `const result =` — generic names | 🟡 SLOP |
| `console.log()` in production paths | 🟡 SLOP |
| `print()` debug statements | 🟡 SLOP |
| `: any` — TypeScript escape hatch | 🟡 SLOP |
| `fetch()` with no timeout | 🟡 SLOP |
| `.catch(console.error)` — swallows after logging | 🟡 SLOP |
| `// This function handles...` — obvious comments | 🔵 MINOR |
| `// TODO fix later` — no ticket reference | 🔵 MINOR |
| Magic numbers (`86400000`, `9999`) | 🔵 MINOR |

### UI
| Pattern | Severity |
|---|---|
| `fontFamily: 'Inter'` / `'Roboto'` — AI default fonts | 🟡 SLOP |
| `from-purple`, `#7C3AED` — AI signature color | 🟡 SLOP |
| `Lorem ipsum` placeholder | 🟡 SLOP |
| `z-index: 9999` — arbitrary stacking | 🟡 SLOP |
| `!important` — specificity hack | 🟡 SLOP |
| `div onClick` with no `aria` role | 🟡 SLOP |
| `rounded-full` on non-pill elements | 🔵 MINOR |
| `shadow-lg` as default | 🔵 MINOR |
| `hover:opacity-80` lazy interaction | 🔵 MINOR |
| `grid-cols-3` equal card grid | 🔵 MINOR |
| `John Doe` / `Jane Doe` placeholders | 🔵 MINOR |

### Prose (`.md`, `.txt`)
| Pattern | Severity |
|---|---|
| `Certainly!`, `Of course!`, `Great question` | 🔴 REBUILD |
| `delve`, `tapestry`, `multifaceted` | 🔴 REBUILD |
| `in today's fast-paced world` | 🔴 REBUILD |
| `Let me explain...` | 🟡 SLOP |
| `leverage`, `utilize`, `seamless`, `cutting-edge` | 🟡 SLOP |
| `furthermore`, `moreover`, `needless to say` | 🟡 SLOP |
| `paradigm shift`, `game-changer`, `synergy` | 🟡 SLOP |
| `at its core`, `let's unpack`, `speaks volumes` | 🟡 SLOP |
| `testament to`, `navigate the landscape` | 🟡 SLOP |
| `it's worth noting`, `In conclusion,` | 🟡 SLOP |
| `robust`, `nuanced`, `compelling`, `crucial` | 🔵 MINOR |

> Full list: 58 rules across code, UI, and prose. See [`scanner/rules.py`](scanner/rules.py).

---

## Install

**Claude Code**
```bash
claude plugin install github:Serhii-Leniv/anti-slop
```

**Cursor**
```bash
git clone https://github.com/Serhii-Leniv/anti-slop
cd anti-slop && ./install.sh cursor
```

**Google Antigravity**
```bash
git clone https://github.com/Serhii-Leniv/anti-slop
cd anti-slop && ./install.sh antigravity
```

**All platforms at once**
```bash
git clone https://github.com/Serhii-Leniv/anti-slop
cd anti-slop && ./install.sh all
```

> Antigravity doesn't support hooks yet — `/no-slop` runs manually only. Auto-firing works on Claude Code and Cursor.

---

## First Run

After installing, personalize rules for your project:

```bash
/no-slop init
```

This scans your existing codebase and builds a profile. If your design system uses Inter — it gets allowlisted. If you already use `console.log` heavily in a debug utility — allowlisted. Rules adapt to you, not the other way around.

---

## Usage

**It runs automatically.** Just write code normally. When slop is found:

```
[anti-slop] 3 finding(s) in src/auth.ts:
  L45: [REBUILD] swallowed exception — hides errors silently
  L12: [SLOP] generic name 'data' — name what it actually contains
  L78: [SLOP] console.log in production path — use structured logger
Fix before continuing.
```

Claude reads this, fixes the issues, moves on. You don't intervene.

**Manual commands:**

| Command | What it does |
|---|---|
| `/no-slop` | Deep review of recent files — full subagent, line-by-line with rewrites |
| `/no-slop init` | Scan codebase, build personal allowlist profile |
| `/no-slop log` | Show minor findings that were silently logged |
| `/no-slop stats` | Finding counts by rule for this session |
| `/no-slop reset` | Delete profile, start fresh |

---

## Token Cost

Detection is local — no LLM involved until something is actually found.

| Event | Tokens |
|---|---|
| Clean file written | 0 |
| Minor finding (severity 1) | 0 — silent log only |
| Real slop found | ~200 |
| Claude fixing from report | ~300–500 (uses existing context) |
| `/no-slop` deep manual review | ~3,000 |
| **Typical full session** | **~400–2,000 total** |

One MCP server costs ~18,000 tokens **per turn**. This plugin costs less than that per session.

---

## Customize

Add your own rules to `scanner/rules.py`:

```python
{
    "id": "my_custom_rule",
    "pattern": r"your_regex_here",
    "message": "what this means and why it's slop",
    "severity": 2,  # 1=minor, 2=slop, 3=rebuild
    "file_types": [".ts", ".tsx"],
}
```

Allowlist rules that are intentional in your project (`~/.claude/anti-slop-profile.json`):
```json
{
  "allowlist_rules": ["inter_font", "console_log"]
}
```

---

## Contributing

PRs welcome. To add rules — edit `scanner/rules.py`, test with the smoke test, submit PR.

```bash
cd scanner && python3 -c "
from detect import scan_file, format_report
import tempfile, os
# write a test file with your pattern, verify it fires
"
```

## License

MIT
