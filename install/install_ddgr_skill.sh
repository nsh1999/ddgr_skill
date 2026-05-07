#!/usr/bin/env bash
# Install ddgr-skill as a Claude Code or Hermes skill
set -euo pipefail

# Defaults
TARGET="hermes"
INSTALL_METHOD="uv"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
         --target)
            TARGET="$2"
            shift 2
             ;;
         --install-method)
            INSTALL_METHOD="$2"
            shift 2
             ;;
         *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--target claude|hermes|all] [--install-method uv|pip]"
            exit 1
             ;;
    esac
done

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Installing ddgr-skill for target: $TARGET (method: $INSTALL_METHOD)..."

# Check ddgr is installed
if ! command -v ddgr &>/dev/null; then
    echo "ERROR: ddgr not found. Install it first:"
    echo "  brew install ddgr"
    exit 1
fi

# Check Python dependencies are installed
if [ "$INSTALL_METHOD" = "uv" ]; then
    if ! command -v uv &>/dev/null; then
        echo "ERROR: uv not found. Install it first:"
        echo "  curl -sSf https://astral.sh/uv | sh"
        exit 1
    fi
fi

cd "$REPO_DIR"

if [ "$INSTALL_METHOD" = "uv" ]; then
    uv sync
    uv pip install -e .
else
    python -m pip install --break-system-packages -e .
fi

# Create wrapper script in ~/.local/bin/ (shared by both agents)
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/ddgr-skill" <<< EOF
#!/bin/bash
exec "$REPO_DIR/.venv/bin/python" -m ddgr_skill "\$@"
EOF
chmod +x "$HOME/.local/bin/ddgr-skill"

# Define target paths
CLAUDE_SKILL_DIR="$HOME/.claude/skills/ddgr-skill"
HERMES_SKILL_DIR="$HOME/.hermes/skills/web/ddgr-skill"

install_skill() {
    local dir="$1"
    local name="$2"
    echo "Installing skill definition to $dir..."
    mkdir -p "$dir"
    cp "$REPO_DIR/skills/ddgr-skill/SKILL.md" "$dir/"
    echo "✅ Installed for $name: $dir/SKILL.md"
}

# Perform installation based on target
case $TARGET in
    claude)
        install_skill "$CLAUDE_SKILL_DIR" "Claude Code"
         ;;
    hermes)
        install_skill "$HERMES_SKILL_DIR" "Hermes"
         ;;
    all)
        install_skill "$CLAUDE_SKILL_DIR" "Claude Code"
        install_skill "$HERMES_SKILL_DIR" "Hermes"
         ;;
     *)
        echo "ERROR: Invalid target '$TARGET'. Supported targets: claude, hermes, all."
        exit 1
         ;;
esac

echo ""
echo "ddgr-skill installed successfully!"
echo "CLI:   ddgr-skill search 'your query' --fetch"
echo "Run:   ddgr-skill lookup 'your query'"
echo ""
echo "Restart your agent session to activate the skill."
