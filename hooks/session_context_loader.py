#!/usr/bin/env python3
"""
Enhanced SessionStart Hook - Shows cached context AND accumulated project data
Displays: priority content, previously touched files, common commands
"""

import json
import sys
import os
import hashlib
from pathlib import Path

STORE_DIR = Path.home() / ".claude" / ".session_store"
CACHE_FILE = STORE_DIR / "permanent_cache.json"
PROJECTS_DIR = STORE_DIR / "projects"

def get_project_id(path):
    return hashlib.md5(path.encode()).hexdigest()[:12]

def load_project_context(cwd):
    """Load accumulated project context from previous sessions"""
    project_id = get_project_id(cwd)
    project_file = PROJECTS_DIR / f"{project_id}.json"

    if project_file.exists():
        try:
            return json.loads(project_file.read_text())
        except:
            return None
    return None

def load_priority_cache(cwd):
    """Load relevant priority cache entries"""
    project_name = Path(cwd).name.lower()
    parent_name = Path(cwd).parent.name.lower()

    output_lines = []
    entries_found = []

    if not CACHE_FILE.exists():
        return None, []

    try:
        cache = json.loads(CACHE_FILE.read_text())
    except:
        return None, []

    for key, val in cache.items():
        key_lower = key.lower()
        desc_lower = val.get("description", "").lower()

        if (project_name in key_lower or project_name in desc_lower or
            parent_name in key_lower or parent_name in desc_lower):

            entries_found.append(key)
            content = val.get("content", "")
            preview = content[:600] if len(content) > 600 else content

            output_lines.append(f"\n[PRIORITY] {key}")
            output_lines.append(f"  {val.get('description', 'N/A')}")
            output_lines.append(f"  {preview[:200]}..." if len(preview) > 200 else f"  {preview}")

    return "\n".join(output_lines) if output_lines else None, entries_found

def main():
    try:
        hook_input = json.load(sys.stdin)
    except:
        hook_input = {}

    cwd = os.getcwd()
    project_name = Path(cwd).name

    # Load both priority cache and project context
    cache_content, priority_entries = load_priority_cache(cwd)
    project_ctx = load_project_context(cwd)

    sections = []

    # Project stats
    if project_ctx:
        session_count = len(project_ctx.get("sessions", []))
        files_touched = project_ctx.get("accumulated_files", [])
        commands = project_ctx.get("accumulated_commands", [])

        sections.append(f"Sessions: {session_count} | Files touched: {len(files_touched)}")

        # Show recent files (last 10)
        if files_touched:
            recent_files = files_touched[-10:]
            sections.append(f"\nRecent files:")
            for f in recent_files:
                sections.append(f"  - {f}")

        # Show common commands (last 5)
        if commands:
            sections.append(f"\nCommon commands:")
            for cmd in commands[-5:]:
                sections.append(f"  $ {cmd[:80]}")

    # Priority content
    if cache_content:
        sections.append(f"\n{cache_content}")

    if sections:
        content = "\n".join(sections)
        message = f"""
╔══════════════════════════════════════════════════════════════╗
║  PROJECT CONTEXT: {project_name[:40]:<40} ║
╚══════════════════════════════════════════════════════════════╝
{content}
"""
    else:
        message = f"""
╔══════════════════════════════════════════════════════════════╗
║  NEW PROJECT: {project_name[:44]:<44} ║
║  Context will accumulate as you work.                        ║
╚══════════════════════════════════════════════════════════════╝
"""

    output = {
        "continue": True,
        "message": message
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
