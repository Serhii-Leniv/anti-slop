#!/usr/bin/env bash
# anti-slop installer
# Detects platform and installs accordingly.
# Usage: ./install.sh [claude|cursor|antigravity|all]

set -e

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-all}"

install_claude() {
  echo "[anti-slop] Installing for Claude Code..."
  claude plugin install "$PLUGIN_DIR" 2>/dev/null || \
    echo "  Manual install: claude --plugin-dir $PLUGIN_DIR"
}

install_cursor() {
  echo "[anti-slop] Installing for Cursor..."
  CURSOR_PLUGINS_DIR="$HOME/.cursor/plugins"
  mkdir -p "$CURSOR_PLUGINS_DIR"
  ln -sf "$PLUGIN_DIR" "$CURSOR_PLUGINS_DIR/anti-slop"
  # copy cursor-specific hooks.json as the active hooks config
  cp "$PLUGIN_DIR/hooks/cursor-hooks.json" "$PLUGIN_DIR/hooks/hooks-cursor-active.json"
  echo "  Linked to $CURSOR_PLUGINS_DIR/anti-slop"
  echo "  Restart Cursor to activate."
}

install_antigravity() {
  echo "[anti-slop] Installing for Google Antigravity..."
  # Antigravity uses Skills only (no hooks yet)
  # Global skills location: ~/.gemini/antigravity/skills/
  AG_SKILLS_DIR="$HOME/.gemini/antigravity/skills/no-slop"
  mkdir -p "$AG_SKILLS_DIR"
  cp "$PLUGIN_DIR/skills/no-slop/SKILL.md" "$AG_SKILLS_DIR/SKILL.md"
  # copy scanner so /no-slop init works
  cp -r "$PLUGIN_DIR/scanner" "$AG_SKILLS_DIR/scanner"
  echo "  Installed skill to $AG_SKILLS_DIR"
  echo "  Note: Antigravity doesn't support hooks yet — use /no-slop manually."
}

case "$TARGET" in
  claude)      install_claude ;;
  cursor)      install_cursor ;;
  antigravity) install_antigravity ;;
  all)
    install_claude
    install_cursor
    install_antigravity
    ;;
  *)
    echo "Usage: ./install.sh [claude|cursor|antigravity|all]"
    exit 1
    ;;
esac

echo ""
echo "[anti-slop] Done. Run /no-slop init in your project to personalize rules."
