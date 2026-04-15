#!/bin/bash
# Fishing Frenzy Agent — Setup Script
# Run this after installing the skill to register the MCP server.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_PATH="$REPO_DIR/ff_agent/server.py"
CONFIG_PATH="$REPO_DIR/CONFIG.md"

echo ""
echo "  🎣 Fishing Frenzy Agent Setup"
echo "  ══════════════════════════════"
echo ""

# Step 1: Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "  ERROR: python3 not found. Install Python 3.10+ first."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python: $PY_VERSION"

# Step 2: Install dependencies
echo "  Installing dependencies..."
pip3 install -q -r "$REPO_DIR/requirements.txt" 2>/dev/null
echo "  Dependencies installed."

# Step 3: Register MCP server
echo ""
if command -v claude &> /dev/null; then
    echo "  Registering MCP server..."
    claude mcp add fishing-frenzy -- python3 "$SERVER_PATH" 2>/dev/null && \
        echo "  MCP server registered." || \
        echo "  MCP server already registered (or run manually: claude mcp add fishing-frenzy -- python3 $SERVER_PATH)"
else
    echo "  WARNING: 'claude' CLI not found in PATH."
    echo "  Register the MCP server manually:"
    echo ""
    echo "    claude mcp add fishing-frenzy -- python3 $SERVER_PATH"
    echo ""
fi

# Step 4: Strategy selection
echo ""
echo "  Choose your starting strategy:"
echo ""
echo "    1) balanced    — Even split: fish, cook, quests (recommended)"
echo "    2) grind       — Max XP, aggressive sushi, short range"
echo "    3) efficiency  — Best gold/energy, long range, cooking focus"
echo ""
read -p "  Strategy [1/2/3, default=1]: " STRATEGY_CHOICE

case "$STRATEGY_CHOICE" in
    2) STRATEGY="grind" ;;
    3) STRATEGY="efficiency" ;;
    *) STRATEGY="balanced" ;;
esac

# Update CONFIG.md with chosen strategy
if [ -f "$CONFIG_PATH" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^STRATEGY: .*/STRATEGY: $STRATEGY/" "$CONFIG_PATH"
    else
        sed -i "s/^STRATEGY: .*/STRATEGY: $STRATEGY/" "$CONFIG_PATH"
    fi
    echo "  Strategy set to: $STRATEGY"
fi

# Done
echo ""
echo "  ══════════════════════════════"
echo "  ✅ Setup complete!"
echo ""
echo "  Start playing:"
echo "    1. Open Claude Code (restart if already open)"
echo "    2. Type: /play"
echo ""
echo "  Edit CONFIG.md to customize thresholds."
echo "  Edit SKILL.md to change the game strategy."
echo ""
