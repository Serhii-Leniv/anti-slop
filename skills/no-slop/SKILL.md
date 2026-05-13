---
name: no-slop
description: Manual deep review of AI slop in code, UI, and prose. Also manages profile.
invocation: /no-slop
---

## Commands

### /no-slop
Deep review of all recently changed files. Runs full subagent analysis — checks not just patterns but principles. Reports every finding with line number and rewrite suggestion.

### /no-slop init
Build personal profile for this project:
```bash
python3 ~/.claude/plugins/anti-slop/scanner/profile_builder.py .
```
Scans existing codebase, learns your patterns, allowlists rules that are intentional.
Saves `.anti-slop-profile.json` in the project root (detected via `.git`/`package.json`/`pyproject.toml`/`go.mod`). Falls back to `~/.claude/anti-slop-profile.json` if no project root found. Commit the file to share allowlists across your team.

### /no-slop log
Show recent silently-logged minor findings:
```bash
tail -50 ~/.claude/anti-slop-log.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    f = json.loads(line)
    print(f\"{f['file']}:{f['line']} [{f['severity_label']}] {f['message']}\")
"
```

### /no-slop reset
Delete profile and start fresh:
```bash
rm -f .anti-slop-profile.json ~/.claude/anti-slop-profile.json
```

### /no-slop stats
Show finding counts for current session:
```bash
python3 -c "
import json, collections
counts = collections.Counter()
try:
    for line in open('${HOME}/.claude/anti-slop-log.jsonl'):
        f = json.loads(line)
        counts[f['rule_id']] += 1
except: pass
for rule, count in counts.most_common(10):
    print(f'{count:4d}  {rule}')
"
```

---

## When Claude Runs Deep Review

Use a fresh subagent with no prior context. Evaluate each finding against:

1. **Is this actually slop or intentional?** Generic names in tests = fine. `console.log` in a debug utility = fine.
2. **Severity**: Is this a silent failure risk (rebuild), design intent issue (slop), or just a style preference (minor)?
3. **Provide a concrete rewrite** — not just "rename this" but show the better version.

Format each finding:
```
file.ts:45 [REBUILD] swallowed exception
  Current:  catch(e) {}
  Fix:      catch(e) { logger.error('auth failed', e); throw new AuthError(e); }

file.tsx:12 [SLOP] Inter font — no design intent
  Current:  fontFamily: 'Inter'
  Fix:      Remove or replace with your design system font token
```
