# anti-slop

Auto-detects AI slop in code, UI, and prose. Fires on every Write/Edit. Zero LLM cost for detection.

## What it catches

**Code** — swallowed exceptions, generic names (`data`, `result`), `console.log` in prod, TypeScript `any`, magic numbers, `fetch()` with no timeout

**UI** — Inter font, purple gradients, `rounded-full` everywhere, `shadow-lg` default, John Doe placeholders, 3-col card grids

**Prose** — "delve", "leverage", "certainly", "it's worth noting", "in conclusion", "let me explain"

## How it works

```
Every Write/Edit
  → local regex scan (0 tokens)
  → if severity ≥ 2: stderr report → Claude fixes inline
  → if severity = 1: silent log
  → never blocks the write
```

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

> **Note:** Antigravity doesn't support hooks yet — `/no-slop` runs manually only. Auto-firing works on Claude Code and Cursor.

## First run

```bash
/no-slop init   # scan your codebase, build personal profile
```

## Commands

| Command | What it does |
|---|---|
| `/no-slop` | Deep manual review of recent files |
| `/no-slop init` | Build personal profile from your codebase |
| `/no-slop log` | Show minor findings logged silently |
| `/no-slop stats` | Finding counts by rule |
| `/no-slop reset` | Delete profile, start fresh |

## Token cost

| Event | Tokens |
|---|---|
| Clean file | 0 |
| Minor finding (severity 1) | 0 (silent log) |
| Real slop found | ~200 |
| `/no-slop` deep review | ~3,000 |
| Typical session | ~400–2,000 total |

## Customize

Add rules to `scanner/rules.py`. Run `/no-slop init` to allowlist patterns already in your codebase.

To allowlist a rule manually, edit `~/.claude/anti-slop-profile.json`:
```json
{
  "allowlist_rules": ["inter_font", "console_log"]
}
```
