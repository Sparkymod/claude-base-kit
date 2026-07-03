#!/usr/bin/env sh
# Installs (or updates) the claude-base-kit into a host project's .claude/ directory.
# NEVER overwrites an existing file — on a name collision the host's file wins and the
# kit file is skipped (reported). Idempotent: re-run to pick up new kit files.
#
# Usage: ./install.sh /path/to/your-project

set -eu

TARGET="${1:?Usage: install.sh /path/to/target-project}"

if [ ! -d "$TARGET" ]; then
    echo "ERROR: target directory not found: $TARGET" >&2
    exit 1
fi

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DIR="$TARGET/.claude"

INSTALLED=0
SKIPPED=0

copy_kit_files() {
    src_subdir="$1"; dest_subdir="$2"
    src="$KIT_ROOT/$src_subdir"
    dst="$CLAUDE_DIR/$dest_subdir"
    mkdir -p "$dst"
    for file in "$src"/*.md; do
        [ -e "$file" ] || continue
        base="$(basename "$file")"
        if [ -e "$dst/$base" ]; then
            echo "    = .claude/$dest_subdir/$base (skipped — host file wins)"
            SKIPPED=$((SKIPPED + 1))
        else
            cp "$file" "$dst/$base"
            echo "    + .claude/$dest_subdir/$base"
            INSTALLED=$((INSTALLED + 1))
        fi
    done
}

echo ""
echo "claude-base-kit install -> $TARGET"

copy_kit_files "core/agents"     "agents"
copy_kit_files "core/principles" "principles"
copy_kit_files "core/pipelines"  "pipelines"
copy_kit_files "core/templates"  "templates"

# Seed the stack contract into rules/ if the host doesn't have one yet
mkdir -p "$CLAUDE_DIR/rules"
if [ -e "$CLAUDE_DIR/rules/stack-contract.md" ]; then
    echo "    = .claude/rules/stack-contract.md (skipped — host file wins)"
    SKIPPED=$((SKIPPED + 1))
else
    cp "$KIT_ROOT/core/templates/stack-contract.md" "$CLAUDE_DIR/rules/stack-contract.md"
    echo "    + .claude/rules/stack-contract.md  (fill this in!)"
    INSTALLED=$((INSTALLED + 1))
fi

# Local knowledge capture directory
if [ ! -d "$CLAUDE_DIR/lessons" ]; then
    mkdir -p "$CLAUDE_DIR/lessons"
    : > "$CLAUDE_DIR/lessons/.gitkeep"
    echo "    + .claude/lessons/"
    INSTALLED=$((INSTALLED + 1))
fi

echo ""
echo "  Installed: $INSTALLED   Skipped (host wins): $SKIPPED"
echo ""
echo "Next steps:"
echo "  1. Fill .claude/rules/stack-contract.md (agents BLOCK without it)."
echo "  2. No CLAUDE.md in the host? Start from .claude/templates/CLAUDE.skeleton.md."
echo "  3. Feature-sized work: run the sdlc-feature pipeline (.claude/pipelines/)."
