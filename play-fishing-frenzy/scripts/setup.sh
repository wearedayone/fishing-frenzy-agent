#!/bin/bash
# Fishing Frenzy Agent — Setup Script
# Installs dependencies and registers the MCP server for every detected AI tool.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_PATH="$REPO_DIR/ff_agent/server.py"
VENV_DIR="$REPO_DIR/.venv"
CONFIGURED=()

echo ""
echo "  🎣 Fishing Frenzy Agent Setup"
echo "  ══════════════════════════════"
echo ""

# ─── Step 1: Check Python 3 ───────────────────────────────────────────────
if ! command -v python3 &> /dev/null; then
    echo "  ERROR: python3 not found. Install Python 3.10+ first."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python: $PY_VERSION"

# ─── Step 2: Install dependencies ─────────────────────────────────────────
echo "  Installing dependencies..."
PYTHON_CMD="python3"

if pip3 install -q -r "$REPO_DIR/requirements.txt" 2>/dev/null; then
    echo "  Dependencies installed (system)."
elif python3 -m pip install -q -r "$REPO_DIR/requirements.txt" 2>/dev/null; then
    echo "  Dependencies installed (system)."
else
    echo "  System pip blocked (PEP 668). Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q -r "$REPO_DIR/requirements.txt"
    PYTHON_CMD="$VENV_DIR/bin/python3"
    echo "  Dependencies installed (venv)."
fi

# ─── Step 3: Register MCP server for every detected AI tool ───────────────
echo ""
echo "  Detecting AI tools..."

# --- Claude Code ---
if command -v claude &> /dev/null; then
    echo "  Found: Claude Code"
    if claude mcp add fishing-frenzy --scope user -- "$PYTHON_CMD" "$SERVER_PATH" 2>&1; then
        CONFIGURED+=("Claude Code")
    else
        CONFIGURED+=("Claude Code (already registered)")
    fi
fi

# --- Cursor ---
CURSOR_DIR="$HOME/.cursor"
CURSOR_MCP="$CURSOR_DIR/mcp.json"
if [ -d "$CURSOR_DIR" ] || command -v cursor &> /dev/null; then
    echo "  Found: Cursor"
    mkdir -p "$CURSOR_DIR"
    if [ -f "$CURSOR_MCP" ]; then
        if python3 -c "
import json, sys
with open('$CURSOR_MCP') as f:
    cfg = json.load(f)
servers = cfg.get('mcpServers', cfg)
if 'fishing-frenzy' not in servers:
    servers['fishing-frenzy'] = {'command': '$PYTHON_CMD', 'args': ['$SERVER_PATH']}
    if 'mcpServers' in cfg:
        cfg['mcpServers'] = servers
    else:
        cfg = servers
    with open('$CURSOR_MCP', 'w') as f:
        json.dump(cfg, f, indent=2)
    sys.exit(0)
else:
    sys.exit(1)
" 2>/dev/null; then
            CONFIGURED+=("Cursor")
        else
            CONFIGURED+=("Cursor (already registered)")
        fi
    else
        echo '{"mcpServers":{"fishing-frenzy":{"command":"'"$PYTHON_CMD"'","args":["'"$SERVER_PATH"'"]}}}' | python3 -m json.tool > "$CURSOR_MCP"
        CONFIGURED+=("Cursor")
    fi
fi

# --- Cline ---
CLINE_DIR="$HOME/.cline"
CLINE_MCP="$CLINE_DIR/mcp_settings.json"
if [ -d "$CLINE_DIR" ]; then
    echo "  Found: Cline"
    if [ -f "$CLINE_MCP" ]; then
        if python3 -c "
import json, sys
with open('$CLINE_MCP') as f:
    cfg = json.load(f)
servers = cfg.setdefault('mcpServers', {})
if 'fishing-frenzy' not in servers:
    servers['fishing-frenzy'] = {'command': '$PYTHON_CMD', 'args': ['$SERVER_PATH']}
    with open('$CLINE_MCP', 'w') as f:
        json.dump(cfg, f, indent=2)
    sys.exit(0)
else:
    sys.exit(1)
" 2>/dev/null; then
            CONFIGURED+=("Cline")
        else
            CONFIGURED+=("Cline (already registered)")
        fi
    else
        mkdir -p "$CLINE_DIR"
        echo '{"mcpServers":{"fishing-frenzy":{"command":"'"$PYTHON_CMD"'","args":["'"$SERVER_PATH"'"]}}}' | python3 -m json.tool > "$CLINE_MCP"
        CONFIGURED+=("Cline")
    fi
fi

# --- Windsurf ---
WINDSURF_DIR="$HOME/.windsurf"
WINDSURF_MCP="$WINDSURF_DIR/mcp.json"
if [ -d "$WINDSURF_DIR" ] || command -v windsurf &> /dev/null; then
    echo "  Found: Windsurf"
    mkdir -p "$WINDSURF_DIR"
    if [ -f "$WINDSURF_MCP" ]; then
        if python3 -c "
import json, sys
with open('$WINDSURF_MCP') as f:
    cfg = json.load(f)
servers = cfg.get('mcpServers', cfg)
if 'fishing-frenzy' not in servers:
    servers['fishing-frenzy'] = {'command': '$PYTHON_CMD', 'args': ['$SERVER_PATH']}
    if 'mcpServers' in cfg:
        cfg['mcpServers'] = servers
    else:
        cfg = servers
    with open('$WINDSURF_MCP', 'w') as f:
        json.dump(cfg, f, indent=2)
    sys.exit(0)
else:
    sys.exit(1)
" 2>/dev/null; then
            CONFIGURED+=("Windsurf")
        else
            CONFIGURED+=("Windsurf (already registered)")
        fi
    else
        echo '{"mcpServers":{"fishing-frenzy":{"command":"'"$PYTHON_CMD"'","args":["'"$SERVER_PATH"'"]}}}' | python3 -m json.tool > "$WINDSURF_MCP"
        CONFIGURED+=("Windsurf")
    fi
fi

# --- OpenClaw ---
if command -v openclaw &> /dev/null; then
    echo "  Found: OpenClaw"
    openclaw mcp set fishing-frenzy '{"command":"'"$PYTHON_CMD"'","args":["'"$SERVER_PATH"'"]}' 2>/dev/null && \
        CONFIGURED+=("OpenClaw") || \
        CONFIGURED+=("OpenClaw (already registered)")
fi

# ─── Step 4: Preferences questionnaire ────────────────────────────────────
echo ""
python3 "$SCRIPT_DIR/setup_preferences.py"

# ─── Summary ──────────────────────────────────────────────────────────────
echo ""
echo "  ══════════════════════════════"

if [ ${#CONFIGURED[@]} -eq 0 ]; then
    echo "  ⚠️  No AI tools detected."
    echo ""
    echo "  Register the MCP server manually for your tool:"
    echo "    Server: $PYTHON_CMD $SERVER_PATH"
    echo ""
    echo "  Claude Code:  claude mcp add fishing-frenzy -- $PYTHON_CMD $SERVER_PATH"
    echo "  Cursor:       Add to ~/.cursor/mcp.json"
    echo "  Cline:        Add to ~/.cline/mcp_settings.json"
    echo "  Windsurf:     Add to ~/.windsurf/mcp.json"
    echo "  OpenClaw:     openclaw mcp set fishing-frenzy '{...}'"
else
    echo "  ✅ Setup complete!"
    echo ""
    echo "  MCP server registered for:"
    for tool in "${CONFIGURED[@]}"; do
        echo "    • $tool"
    done
fi

echo ""
echo "  Next steps:"
echo "    1. Restart your AI tool"
echo "    2. Type: /play-fishing-frenzy"
echo ""
