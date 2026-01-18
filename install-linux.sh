#!/bin/bash
# Claude Code Context Cache - Linux/WSL Installer

set -e

CLAUDE_DIR="$HOME/.claude"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Claude Code Context Cache System..."

# Create directories
mkdir -p "$CLAUDE_DIR/hooks"
mkdir -p "$CLAUDE_DIR/mcp-servers/context-store"
mkdir -p "$CLAUDE_DIR/.session_store/projects"

# Copy files
cp "$SCRIPT_DIR/hooks/"*.py "$CLAUDE_DIR/hooks/"
cp "$SCRIPT_DIR/mcp-servers/context-store/server.py" "$CLAUDE_DIR/mcp-servers/context-store/"

# Make executable
chmod +x "$CLAUDE_DIR/hooks/"*.py
chmod +x "$CLAUDE_DIR/mcp-servers/context-store/server.py"

# Check if settings.json exists
if [ -f "$CLAUDE_DIR/settings.json" ]; then
    echo "settings.json exists - please manually merge the following config:"
    cat << 'EOF'

Add to your settings.json:
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/init_context.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/session_context_loader.py"}
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/save_context.py"}
        ]
      }
    ]
  },
  "mcpServers": {
    "context-store": {
      "command": "python3",
      "args": ["/home/$USER/.claude/mcp-servers/context-store/server.py"]
    }
  }
}
EOF
else
    # Create settings.json
    cat > "$CLAUDE_DIR/settings.json" << EOF
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/init_context.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/session_context_loader.py"}
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/save_context.py"}
        ]
      }
    ]
  },
  "mcpServers": {
    "context-store": {
      "command": "python3",
      "args": ["$HOME/.claude/mcp-servers/context-store/server.py"]
    }
  }
}
EOF
    echo "Created settings.json"
fi

echo ""
echo "Installation complete!"
echo "Restart Claude Code to activate."
