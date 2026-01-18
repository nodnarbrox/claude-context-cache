# Claude Code Context Cache System - Complete Documentation

> **Purpose**: Persistent memory across sessions for Claude Code and other LLMs
> **Version**: 1.0.0
> **Last Updated**: 2026-01-18

---

## System Overview

The Context Cache System provides **persistent memory** across Claude Code sessions. It consists of:

1. **Python Hooks** - Automatically load/save context at session start/end
2. **MCP Server** (`context-store`) - 12 tools for manual context management
3. **JSON Storage** - File-based persistence in `~/.claude/.session_store/`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE SESSION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  SESSION START   │  │  DURING SESSION  │  │  SESSION END   │ │
│  │  (Python Hooks)  │  │  (PostToolUse)   │  │ (Python Hooks) │ │
│  │  init_context.py │  │  live_cache.py   │  │ save_context.py│ │
│  │  session_loader  │  │  ↓ REAL-TIME ↓   │  └───────┬────────┘ │
│  └────────┬─────────┘  └────────┬─────────┘          │          │
│           │                     │                     │          │
│           │            Tracks every:                  │          │
│           │            - File Edit/Write              │          │
│           │            - File Read                    │          │
│           │            - Bash command                 │          │
│           ▼                     ▼                     ▼          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   MCP SERVER (context-store)               │ │
│  │  12 Tools: store_project_context, get_project_context,    │ │
│  │  store_priority_content, get_priority_content, etc.       │ │
│  └──────────────────────────┬─────────────────────────────────┘ │
│                              │                                    │
└──────────────────────────────┼────────────────────────────────────┘
                               ▼
              ┌────────────────────────────────┐
              │     ~/.claude/.session_store/   │
              ├────────────────────────────────┤
              │  permanent_cache.json          │  ← Priority content (never deleted)
              │  global_context.json           │  ← Global cache (all projects)
              │  cached_plans.json             │  ← Development plans
              │  projects/{hash}.json          │  ← Per-project context
              │  live_session.json             │  ← REAL-TIME tracking (current session)
              └────────────────────────────────┘
```

## Live Caching (Real-Time Tracking)

The system now tracks activity **as you work**, not just at session end.

### What Gets Tracked Automatically:
- **Files Modified** - Every Edit, Write, NotebookEdit (last 50)
- **Files Read** - Every Read operation (last 100)
- **Commands Run** - Every Bash command (last 30)
- **Errors Encountered** - Failed commands with error output

### How It Works:
```
PostToolUse Hook (Edit|Write|Read|Bash|NotebookEdit)
        ↓
    live_cache.py
        ↓
    live_session.json (updated in real-time)
        ↓
    Session End → Merged into project context
```

### View Current Session Stats:
```bash
cat ~/.claude/.session_store/live_session.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'Files Modified: {len(d.get(\"files_modified\",[]))}')
print(f'Files Read: {len(d.get(\"files_read\",[]))}')
print(f'Commands Run: {len(d.get(\"commands_run\",[]))}')
"
```

### Session Startup Shows Live Status:
```
╔══════════════════════════════════════════════════════════════╗
║  CONTEXT CACHE LOADED - 3 RELEVANT ENTRIES FOUND             ║
║  [LIVE CACHING: ON] Recording as you work                    ║
╚══════════════════════════════════════════════════════════════╝

[LIVE TRACKING ACTIVE]
  Files Modified: 12
  Files Read: 45
  Commands Run: 8
  Last Update: 2026-01-18T15:30:00
```

---

## File Locations

| File | Purpose | Persistence |
|------|---------|-------------|
| `~/.claude/.session_store/permanent_cache.json` | Priority content | **Never deleted** |
| `~/.claude/.session_store/global_context.json` | Cross-project data | Permanent |
| `~/.claude/.session_store/cached_plans.json` | Development plans | Permanent |
| `~/.claude/.session_store/projects/{id}.json` | Per-project context | Per-project |
| `~/.claude/.session_store/live_session.json` | **Real-time tracking** | Current session |
| `~/.claude/hooks/init_context.py` | Session start hook | N/A |
| `~/.claude/hooks/save_context.py` | Session end hook | N/A |
| `~/.claude/hooks/session_context_loader.py` | Display cached content | N/A |
| `~/.claude/hooks/live_cache.py` | **PostToolUse hook** | N/A |
| `~/.claude/mcp-servers/context-store/server.py` | MCP server | N/A |

---

## MCP Tools Reference

### 1. `store_project_context`
Store context for the current project (directory-specific).

```json
{
  "tool": "store_project_context",
  "arguments": {
    "key": "api_endpoints",
    "value": "POST /api/users - Create user\nGET /api/users/:id - Get user",
    "priority": 8
  }
}
```

**Use case**: Remember project-specific knowledge like API routes, database schema, coding patterns.

---

### 2. `get_project_context`
Retrieve context from the current project.

```json
{
  "tool": "get_project_context",
  "arguments": {
    "key": "api_endpoints"
  }
}

// Or get ALL project context:
{
  "tool": "get_project_context",
  "arguments": {}
}
```

---

### 3. `store_priority_content`
Store priority content that is **NEVER deleted**. Use for critical learnings.

```json
{
  "tool": "store_priority_content",
  "arguments": {
    "content_id": "feature-plan",
    "content": "# Example Project Plan\n...(full plan content)...",
    "description": "Complete implementation plan for voice AI feature"
  }
}
```

**Use case**: Implementation plans, architectural decisions, critical fixes.

---

### 4. `get_priority_content`
Retrieve priority content by ID or list all.

```json
// Get specific content:
{
  "tool": "get_priority_content",
  "arguments": {
    "content_id": "feature-plan"
  }
}

// List all priority content:
{
  "tool": "get_priority_content",
  "arguments": {}
}
```

---

### 5. `store_global`
Store in global cache (available in ALL projects).

```json
{
  "tool": "store_global",
  "arguments": {
    "key": "server_info",
    "value": "Host: 192.168.1.100\nProxy: Container 101"
  }
}
```

**Use case**: Infrastructure info, credentials references, cross-project knowledge.

---

### 6. `get_global`
Retrieve from global cache.

```json
{
  "tool": "get_global",
  "arguments": {
    "key": "server_info"
  }
}
```

---

### 7. `list_all_projects`
List all known projects with their IDs and session counts.

```json
{
  "tool": "list_all_projects",
  "arguments": {}
}
```

**Returns**:
```
Known Projects:
  [d4dfc6ea779a] my-project - /home/user/my-project (12 sessions)
  [f61bd6155181] medproject - /home/user/other-project (5 sessions)
```

---

### 8. `get_other_project_context`
Access context from a different project.

```json
{
  "tool": "get_other_project_context",
  "arguments": {
    "project_id": "d4dfc6ea779a",
    "key": "database_schema"
  }
}
```

**Use case**: Reference work from another project without switching directories.

---

### 9. `cache_plan`
Cache a development plan for later retrieval.

```json
{
  "tool": "cache_plan",
  "arguments": {
    "plan_name": "per-caller-context-v2",
    "content": "# Implementation Plan\n1. Create database table\n2. Add service layer..."
  }
}
```

---

### 10. `get_cached_plan`
Retrieve a cached plan.

```json
{
  "tool": "get_cached_plan",
  "arguments": {
    "plan_name": "per-caller-context-v2"
  }
}
```

---

### 11. `list_cached_plans`
List all cached plans.

```json
{
  "tool": "list_cached_plans",
  "arguments": {}
}
```

---

### 12. `get_session_history` / `get_project_sessions`
View session history.

```json
{
  "tool": "get_session_history",
  "arguments": {
    "limit": 20
  }
}

{
  "tool": "get_project_sessions",
  "arguments": {
    "project_id": "d4dfc6ea779a"
  }
}
```

---

## Automatic Behavior (Hooks)

### Session Start
When a new session starts, the system automatically:
1. Loads project-specific context
2. Loads global context
3. Displays relevant cached content matching the project name
4. Shows a banner with entry count

**Output Example**:
```
╔══════════════════════════════════════════════════════════════╗
║  CONTEXT CACHE LOADED - 3 RELEVANT ENTRIES FOUND             ║
║  READ THIS BEFORE STARTING WORK!                             ║
╚══════════════════════════════════════════════════════════════╝

Project: my-project
Working Directory: /home/user/my-project

============================================================
CACHED: feature-plan
============================================================
Description: Complete implementation plan for voice AI feature
Content Preview:
# Example Project - Per-Caller Context System
...
```

### Session End
When a session ends, the system automatically:
1. Records session in project history (keeps last 50)
2. Updates global session history (keeps last 100)
3. Preserves all stored context

---

## Best Practices

### When to Store Context

| Situation | Tool to Use | Priority |
|-----------|-------------|----------|
| Project-specific pattern discovered | `store_project_context` | 5-7 |
| Implementation plan created | `store_priority_content` | 10 (auto) |
| Bug fix or critical learning | `store_priority_content` | 10 (auto) |
| Infrastructure info | `store_global` | N/A |
| Multi-step plan | `cache_plan` | N/A |

### Naming Conventions

```
Priority Content IDs:
  {project}-{feature}-plan     → myproject-feature-plan
  {project}-fix-{date}         → myproject-fix-20260118

Project Context Keys:
  database_schema
  api_endpoints
  coding_patterns
  known_issues

Global Keys:
  infrastructure_info
  environment_config
  server_locations
```

### Cache Management

```bash
# Check cache size
du -sh ~/.claude/.session_store/

# View all priority content keys
cat ~/.claude/.session_store/permanent_cache.json | jq 'keys'

# Quick manual check
cd ~/.claude/.session_store && python3 -c "
import json
cache = json.load(open('permanent_cache.json'))
for k,v in cache.items():
    print(f'{k}: {v.get(\"description\",\"\")[:60]}')"
```

---

## Integration with CLAUDE.md

Add this to your project's CLAUDE.md or global ~/.claude/CLAUDE.md:

```markdown
## Context Cache System

### Check Cache FIRST
Before exploring or rebuilding, check if context is cached:
1. Session hook will show cached entries at startup
2. Use `get_project_context` MCP tool for project-specific data
3. Use `get_priority_content` for implementation plans

### Cache Important Findings
After discovering something important:
1. Use `store_priority_content` for plans and critical fixes
2. Use `store_project_context` for project patterns
3. Use `store_global` for infrastructure info

### MCP Tools Available:
- `store_project_context` - Save project-specific knowledge
- `get_project_context` - Retrieve project knowledge
- `store_priority_content` - Save priority content (never deleted)
- `get_priority_content` - Retrieve priority content
- `store_global` / `get_global` - Cross-project data
- `cache_plan` / `get_cached_plan` - Development plans
```

---

## Troubleshooting

### MCP Server Not Responding

```bash
# Check if server is enabled in settings
cat ~/.claude/settings.json | jq '.enabledMcpjsonServers'
# Should include "context-store"

# Test server manually
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 ~/.claude/mcp-servers/context-store/server.py

# Check server path exists
ls -la ~/.claude/mcp-servers/context-store/server.py
```

### Hooks Not Running

```bash
# Check hook configuration
cat ~/.claude/settings.json | jq '.hooks'

# Test hooks manually
python3 ~/.claude/hooks/init_context.py < /dev/null
python3 ~/.claude/hooks/session_context_loader.py < /dev/null
```

### Cache Not Loading

```bash
# Check if cache file exists and is valid JSON
cat ~/.claude/.session_store/permanent_cache.json | jq '.' > /dev/null && echo "Valid JSON" || echo "Invalid JSON"

# Check permissions
ls -la ~/.claude/.session_store/
```

---

## Teaching Other LLMs

To enable another LLM to use this system:

### 1. Explain the Concept
"You have access to a persistent memory system via MCP tools. Important context is cached between sessions. Check cache before rebuilding."

### 2. Provide Tool Descriptions
Copy the MCP Tools Reference section above.

### 3. Set Expectations
- Session start hook will display relevant cached content
- Use `get_project_context` to retrieve stored knowledge
- Use `store_priority_content` for important findings
- Cache is project-aware (based on working directory)

### 4. Example Prompts

```
"Before starting work on the project, check if there's cached context using get_project_context."

"After creating this implementation plan, store it using store_priority_content with ID 'feature-name-plan'."

"This infrastructure info applies to all projects - store it globally using store_global."
```

---

## Storage Schema

### permanent_cache.json
```json
{
  "content-id": {
    "content": "Full content string...",
    "description": "Brief description",
    "priority": 10,
    "stored_at": "2026-01-18T10:30:00.000Z",
    "size_chars": 15000
  }
}
```

### global_context.json
```json
{
  "all_projects": {
    "d4dfc6ea779a": {
      "path": "/home/user/my-project",
      "name": "my-project",
      "last_accessed": "2026-01-18T10:30:00.000Z",
      "session_count": 12
    }
  },
  "global_cache": {
    "key": {
      "value": "stored value",
      "stored_at": "2026-01-18T10:30:00.000Z"
    }
  },
  "session_history": [
    {
      "project_id": "d4dfc6ea779a",
      "project_name": "my-project",
      "end_time": "2026-01-18T10:30:00.000Z"
    }
  ]
}
```

### projects/{hash}.json
```json
{
  "project_path": "/home/user/my-project",
  "project_name": "my-project",
  "sessions": [
    {
      "session_id": "session_20260118_103000",
      "end_time": "2026-01-18T10:30:00.000Z",
      "duration_seconds": 3600
    }
  ],
  "context": {
    "key": {
      "value": "stored value",
      "priority": 5,
      "stored_at": "2026-01-18T10:30:00.000Z"
    }
  },
  "cached_content": {},
  "last_session": "2026-01-18T10:30:00.000Z"
}
```

---

## Quick Reference Card

| Action | Tool | Key Params |
|--------|------|------------|
| Store project knowledge | `store_project_context` | key, value, priority |
| Get project knowledge | `get_project_context` | key (optional) |
| Store critical content | `store_priority_content` | content_id, content, description |
| Get critical content | `get_priority_content` | content_id (optional) |
| Store cross-project | `store_global` | key, value |
| Get cross-project | `get_global` | key (optional) |
| Cache plan | `cache_plan` | plan_name, content |
| Get plan | `get_cached_plan` | plan_name |
| List projects | `list_all_projects` | (none) |
| Get other project | `get_other_project_context` | project_id, key |

---

**Last Updated**: 2026-01-18
**Author**: Claude Code Context Cache System
**Status**: Production-Ready
