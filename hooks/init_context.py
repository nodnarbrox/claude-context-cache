#!/usr/bin/env python3
"""
SessionStart Hook - Initializes context from persistent storage.
Runs at the beginning of every Claude Code session.
Supports: per-project context, multi-session, cross-folder access
"""

import json
import sys
import os
import hashlib
from datetime import datetime
from pathlib import Path

STORE_DIR = Path.home() / ".claude" / ".session_store"
PROJECTS_DIR = STORE_DIR / "projects"
GLOBAL_CONTEXT = STORE_DIR / "global_context.json"

def get_project_id(path):
    """Generate unique ID for a project folder"""
    return hashlib.md5(path.encode()).hexdigest()[:12]

def get_project_file(cwd):
    """Get project-specific context file"""
    project_id = get_project_id(cwd)
    return PROJECTS_DIR / f"{project_id}.json"

def load_project_context(cwd):
    """Load context for current project"""
    project_file = get_project_file(cwd)
    if project_file.exists():
        try:
            with open(project_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        "project_path": cwd,
        "sessions": [],
        "context": {},
        "cached_content": {}
    }

def load_global_context():
    """Load global context (available everywhere)"""
    if GLOBAL_CONTEXT.exists():
        try:
            with open(GLOBAL_CONTEXT, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        "all_projects": {},
        "global_cache": {},
        "session_history": []
    }

def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    cwd = os.getcwd()

    # Create directories
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load both project and global context
    project_context = load_project_context(cwd)
    global_context = load_global_context()

    # Register this project in global index
    project_id = get_project_id(cwd)
    global_context["all_projects"][project_id] = {
        "path": cwd,
        "name": Path(cwd).name,
        "last_accessed": datetime.now().isoformat(),
        "session_count": len(project_context.get("sessions", []))
    }

    # Load available plans
    plans_dir = Path.home() / ".claude" / "plans"
    available_plans = []
    if plans_dir.exists():
        available_plans = [p.name for p in list(plans_dir.glob("*.md"))[-10:]]

    # Build session data
    session_data = {
        "session_start": datetime.now().isoformat(),
        "cwd": cwd,
        "project_id": project_id,
        "project_sessions": len(project_context.get("sessions", [])),
        "global_projects": len(global_context.get("all_projects", {})),
        "project_context": project_context.get("context", {}),
        "global_cache": global_context.get("global_cache", {}),
        "available_plans": available_plans,
        "features": [
            "per_project_context",
            "multi_session_support",
            "cross_folder_access",
            "priority_caching"
        ]
    }

    # Save current session
    current_file = STORE_DIR / "current_session.json"
    with open(current_file, 'w') as f:
        json.dump(session_data, f, indent=2)

    # Save updated global context
    with open(GLOBAL_CONTEXT, 'w') as f:
        json.dump(global_context, f, indent=2)

    output = {
        "continue": True,
        "message": f"Project: {Path(cwd).name} | Sessions: {session_data['project_sessions']} | Projects: {session_data['global_projects']}"
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
