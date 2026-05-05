#!/usr/bin/env bash
# Test ddgr-skill installation on Hermes server (Titan) via SSH
set -euo pipefail

HERMES_USER="hermes"
HERMES_HOST="titan"

echo "🧪 Testing ddgr-skill on $HERMES_HOST..."

ssh $HERMES_USER@$HERMES_HOST <<<EOFEOF
    set -euo pipefail

    echo "Checking CLI..."
    if ~/.local/bin/ddgr-skill --help > /dev/null 2>&1; then
        echo "✅ CLI is accessible"
    else
        echo "❌ CLI not found in ~/.local/bin/ddgr-skill"
        exit 1
    fi

    echo "Checking Skill Definition..."
    if [ -f ~/.hermes/skills/web/ddgr-skill/SKILL.md ]; then
        echo "✅ SKILL.md found in ~/.hermes/skills/web/ddgr-skill/"
    else
        echo "❌ SKILL.md missing from ~/.hermes/skills/web/ddgr-skill/"
        exit 1
    fi

    echo "Running a test lookup..."
    ~/.local/bin/ddgr-skill lookup "test query" --num 1
    if [ $? -eq 0 ]; then
        echo "✅ Lookup command executed successfully"
    else
        echo "❌ Lookup command failed"
        exit 1
    fi

    echo "✨ All tests passed on $HERMES_HOST!"
EOF
