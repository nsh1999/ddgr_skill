#!/usr/bin/env bash
# Install ddgr-skill as a Claude Code or Hermes skill
set -euo pipefail

# Defaults
INSTALL_METHOD="uv"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-method)
            INSTALL_METHOD="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--install-method uv|pip]"
            exit 1
            ;;
    esac
done

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Installing ddgr-skill (method: $INSTALL_METHOD)..."

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

echo ""
echo "ddgr-skill installed successfully!"
echo "Skill definitions are auto-installed on first ddgr-skill run."
echo "CLI:   ddgr-skill search 'your query' --fetch"
echo "Run:   ddgr-skill lookup 'your query'"
echo ""
echo "Restart your agent session to activate the skill."
