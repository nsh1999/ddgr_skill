#!/usr/bin/env bash
# Install ddgr-skill as a Claude Code skill
set -euo pipefail

SKILL_DIR="$HOME/.claude/skills/ddgr-skill"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Installing ddgr-skill..."

# Check ddgr is installed
if ! command -v ddgr &>/dev/null; then
    echo "ERROR: ddgr not found. Install it first:"
    echo "  brew install ddgr"
    exit 1
fi

# Check Python dependencies are installed
if ! command -v uv &>/dev/null; then
    echo "ERROR: uv not found. Install it first:"
    echo "  curl -sSf https://astral.sh/uv | sh"
    exit 1
fi

cd "$REPO_DIR"
uv sync
uv pip install -e .

# Create wrapper script in ~/.local/bin/ (typically in PATH)
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/ddgr-skill" << EOF
#!/bin/bash
exec "$REPO_DIR/.venv/bin/python" -m ddgr_skill "\$@"
EOF
chmod +x "$HOME/.local/bin/ddgr-skill"

# Install skill definition
mkdir -p "$SKILL_DIR"
cp "$REPO_DIR/skills/ddgr-skill/SKILL.md" "$SKILL_DIR/"

echo ""
echo "ddgr-skill installed successfully!"
echo "  Skill: $SKILL_DIR/SKILL.md"
echo "  CLI:   ddgr-skill search 'your query' --fetch"
echo "  Run:   ddgr-skill lookup 'your query'"
echo ""
echo "Restart Claude Code to activate the skill."
