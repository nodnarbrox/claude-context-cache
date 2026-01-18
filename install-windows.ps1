# Claude Code Context Cache - Windows Installer

$ErrorActionPreference = "Stop"

$ClaudeDir = "$env:USERPROFILE\.claude"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Installing Claude Code Context Cache System..."

# Create directories
New-Item -ItemType Directory -Force -Path "$ClaudeDir\hooks" | Out-Null
New-Item -ItemType Directory -Force -Path "$ClaudeDir\mcp-servers\context-store" | Out-Null
New-Item -ItemType Directory -Force -Path "$ClaudeDir\.session_store\projects" | Out-Null

# Copy files
Copy-Item "$ScriptDir\hooks\*.py" "$ClaudeDir\hooks\" -Force
Copy-Item "$ScriptDir\mcp-servers\context-store\server.py" "$ClaudeDir\mcp-servers\context-store\" -Force

# Check if settings.json exists
$SettingsPath = "$ClaudeDir\settings.json"
if (Test-Path $SettingsPath) {
    Write-Host "settings.json exists - please manually merge the following config:"
    Write-Host @"

Add to your settings.json:
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {"type": "command", "command": "python C:/Users/$env:USERNAME/.claude/hooks/init_context.py"},
          {"type": "command", "command": "python C:/Users/$env:USERNAME/.claude/hooks/session_context_loader.py"}
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {"type": "command", "command": "python C:/Users/$env:USERNAME/.claude/hooks/save_context.py"}
        ]
      }
    ]
  },
  "mcpServers": {
    "context-store": {
      "command": "python",
      "args": ["C:/Users/$env:USERNAME/.claude/mcp-servers/context-store/server.py"]
    }
  }
}
"@
} else {
    # Create settings.json
    $Settings = @"
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {"type": "command", "command": "python C:/Users/$env:USERNAME/.claude/hooks/init_context.py"},
          {"type": "command", "command": "python C:/Users/$env:USERNAME/.claude/hooks/session_context_loader.py"}
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {"type": "command", "command": "python C:/Users/$env:USERNAME/.claude/hooks/save_context.py"}
        ]
      }
    ]
  },
  "mcpServers": {
    "context-store": {
      "command": "python",
      "args": ["C:/Users/$env:USERNAME/.claude/mcp-servers/context-store/server.py"]
    }
  }
}
"@
    $Settings | Out-File -FilePath $SettingsPath -Encoding utf8
    Write-Host "Created settings.json"
}

Write-Host ""
Write-Host "Installation complete!"
Write-Host "Restart Claude Code to activate."
