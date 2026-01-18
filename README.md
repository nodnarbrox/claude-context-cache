# Claude Code Context Cache System

Persistent memory across Claude Code sessions. Automatically captures and recalls project context, files edited, commands run, and priority content.

## Features

- **Auto-capture**: SessionEnd hook extracts files edited, commands run from transcript
- **Auto-display**: SessionStart hook shows accumulated context at startup
- **MCP Tools**: 12 tools for manual context management
- **Priority Content**: Never-deleted storage for critical plans/fixes
- **Project-aware**: Context is scoped to working directory

## Quick Install

### Windows
```powershell
.\install-windows.ps1
```

### Linux/WSL
```bash
./install-linux.sh
```

## Manual Install

1. Copy `hooks/` to `~/.claude/hooks/`
2. Copy `mcp-servers/` to `~/.claude/mcp-servers/`
3. Create `~/.claude/.session_store/projects/`
4. Add to `~/.claude/settings.json`:

```json
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
      "args": ["~/.claude/mcp-servers/context-store/server.py"]
    }
  }
}
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `store_project_context` | Save project-specific knowledge |
| `get_project_context` | Retrieve project knowledge |
| `store_priority_content` | Save critical content (never deleted) |
| `get_priority_content` | Retrieve critical content |
| `store_global` / `get_global` | Cross-project data |
| `cache_plan` / `get_cached_plan` | Development plans |
| `list_all_projects` | See all tracked projects |

## Storage

- `~/.claude/.session_store/permanent_cache.json` - Priority content
- `~/.claude/.session_store/global_context.json` - Cross-project data
- `~/.claude/.session_store/projects/{hash}.json` - Per-project context

## Add to CLAUDE.md

```markdown
## Context Cache System

### Check Cache FIRST
1. Session hook will show cached entries at startup
2. Use `get_project_context` MCP tool for project-specific data
3. Use `get_priority_content` for implementation plans

### Cache Important Findings
1. Use `store_priority_content` for plans and critical fixes
2. Use `store_project_context` for project patterns
3. Use `store_global` for infrastructure info
```

See [DOCS.md](DOCS.md) for full documentation.
