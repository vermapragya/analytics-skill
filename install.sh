#!/usr/bin/env bash
# analytics-skills installer
# Copies skills into Claude Code or Cursor skill directories.
#
# Usage:
#   bash install.sh --target claude
#   bash install.sh --target cursor --project-dir /path/to/project
#   bash install.sh --target claude --skills ab-test-analysis,cohort-analysis

set -euo pipefail

TARGET=""
PROJECT_DIR=""
SKILLS_FILTER=""
INCLUDE_AGENTS=false
INCLUDE_COMMANDS=false
INCLUDE_RULES=false
INCLUDE_HOOKS=false

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<EOF
Usage: bash install.sh --target <claude|cursor> [options]

Options:
  --target <claude|cursor>     Required. Where to install.
  --project-dir <path>         For cursor: install into this project's .cursor/skills/
                               If omitted, installs to ~/.cursor/skills/
  --skills a,b,c               Comma-separated skill names. Default: all.
  --with-agents                Also install agents/
  --with-commands              Also install commands/
  --with-rules                 Also install rules/
  --with-hooks                 Also install hooks/
  --all                        Shortcut for --with-agents --with-commands --with-rules --with-hooks
  -h, --help                   Show this help

Examples:
  bash install.sh --target claude --all
  bash install.sh --target cursor --project-dir ~/my-project
  bash install.sh --target claude --skills ab-test-analysis,cohort-analysis
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    --skills) SKILLS_FILTER="$2"; shift 2 ;;
    --with-agents) INCLUDE_AGENTS=true; shift ;;
    --with-commands) INCLUDE_COMMANDS=true; shift ;;
    --with-rules) INCLUDE_RULES=true; shift ;;
    --with-hooks) INCLUDE_HOOKS=true; shift ;;
    --all)
      INCLUDE_AGENTS=true
      INCLUDE_COMMANDS=true
      INCLUDE_RULES=true
      INCLUDE_HOOKS=true
      shift
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "ERROR: --target is required"
  usage
  exit 1
fi

# Resolve install paths
case "$TARGET" in
  claude)
    SKILLS_DEST="$HOME/.claude/skills/analytics"
    AGENTS_DEST="$HOME/.claude/agents"
    COMMANDS_DEST="$HOME/.claude/commands"
    RULES_DEST="$HOME/.claude/rules/analytics"
    HOOKS_DEST="$HOME/.claude/hooks"
    ;;
  cursor)
    if [[ -n "$PROJECT_DIR" ]]; then
      SKILLS_DEST="$PROJECT_DIR/.cursor/skills"
    else
      SKILLS_DEST="$HOME/.cursor/skills"
    fi
    AGENTS_DEST=""
    COMMANDS_DEST=""
    RULES_DEST=""
    HOOKS_DEST=""
    ;;
  *)
    echo "ERROR: --target must be 'claude' or 'cursor'"
    exit 1
    ;;
esac

mkdir -p "$SKILLS_DEST"

if [[ -n "$SKILLS_FILTER" ]]; then
  IFS=',' read -ra SKILLS_ARR <<< "$SKILLS_FILTER"
  for skill in "${SKILLS_ARR[@]}"; do
    if [[ -d "$SCRIPT_DIR/skills/$skill" ]]; then
      cp -R "$SCRIPT_DIR/skills/$skill" "$SKILLS_DEST/"
      echo "  installed skill: $skill"
    else
      echo "  WARNING: skill not found: $skill"
    fi
  done
else
  cp -R "$SCRIPT_DIR"/skills/* "$SKILLS_DEST/"
  echo "  installed all skills -> $SKILLS_DEST"
fi

if [[ "$INCLUDE_AGENTS" == true && -n "$AGENTS_DEST" ]]; then
  mkdir -p "$AGENTS_DEST"
  cp -R "$SCRIPT_DIR"/agents/* "$AGENTS_DEST/" 2>/dev/null || true
  echo "  installed agents -> $AGENTS_DEST"
fi

if [[ "$INCLUDE_COMMANDS" == true && -n "$COMMANDS_DEST" ]]; then
  mkdir -p "$COMMANDS_DEST"
  cp -R "$SCRIPT_DIR"/commands/* "$COMMANDS_DEST/" 2>/dev/null || true
  echo "  installed commands -> $COMMANDS_DEST"
fi

if [[ "$INCLUDE_RULES" == true && -n "$RULES_DEST" ]]; then
  mkdir -p "$RULES_DEST"
  cp -R "$SCRIPT_DIR"/rules/* "$RULES_DEST/" 2>/dev/null || true
  echo "  installed rules -> $RULES_DEST"
fi

if [[ "$INCLUDE_HOOKS" == true && -n "$HOOKS_DEST" ]]; then
  mkdir -p "$HOOKS_DEST"
  cp "$SCRIPT_DIR"/hooks/hooks.json "$HOOKS_DEST/hooks.json" 2>/dev/null || true
  echo "  installed hooks -> $HOOKS_DEST/hooks.json"
fi

echo ""
echo "Done. Verify with:"
echo "  ls $SKILLS_DEST"
