#!/usr/bin/env python3
"""
SessionEnd Hook - Auto-captures and persists context for future sessions.
Reads transcript, extracts key info (files, commands, patterns), stores summaries.
"""

import json
import sys
import os
import hashlib
import re
from datetime import datetime
from pathlib import Path

STORE_DIR = Path.home() / ".claude" / ".session_store"
PROJECTS_DIR = STORE_DIR / "projects"
GLOBAL_CONTEXT = STORE_DIR / "global_context.json"

def get_project_id(path):
    return hashlib.md5(path.encode()).hexdigest()[:12]

def get_project_file(cwd):
    project_id = get_project_id(cwd)
    return PROJECTS_DIR / f"{project_id}.json"

def load_json(filepath):
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filepath, data):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def extract_session_context(transcript_path):
    """Extract useful context from the session transcript"""
    context = {
        "files_edited": set(),
        "files_read": set(),
        "commands_run": [],
        "key_findings": [],
        "errors_fixed": []
    }

    if not transcript_path or not Path(transcript_path).exists():
        # Convert sets to lists before returning
        context["files_edited"] = list(context["files_edited"])
        context["files_read"] = list(context["files_read"])
        return context

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())

                    # Extract from tool uses
                    if entry.get("type") == "tool_use":
                        tool = entry.get("name", "")
                        args = entry.get("input", {})

                        if tool == "Edit" and args.get("file_path"):
                            context["files_edited"].add(args["file_path"])
                        elif tool == "Write" and args.get("file_path"):
                            context["files_edited"].add(args["file_path"])
                        elif tool == "Read" and args.get("file_path"):
                            context["files_read"].add(args["file_path"])
                        elif tool == "Bash" and args.get("command"):
                            cmd = args["command"][:100]  # Truncate long commands
                            if cmd not in context["commands_run"]:
                                context["commands_run"].append(cmd)

                    # Extract from tool results for errors/fixes
                    if entry.get("type") == "tool_result":
                        content = str(entry.get("content", ""))
                        if "error" in content.lower() or "fix" in content.lower():
                            snippet = content[:200]
                            if snippet not in context["errors_fixed"]:
                                context["errors_fixed"].append(snippet)

                except json.JSONDecodeError:
                    continue
    except Exception as e:
        pass

    # Convert sets to lists for JSON
    context["files_edited"] = list(context["files_edited"])
    context["files_read"] = list(context["files_read"])
    # Limit lists
    context["commands_run"] = context["commands_run"][:20]
    context["errors_fixed"] = context["errors_fixed"][:10]

    return context

def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    cwd = os.getcwd()
    project_id = get_project_id(cwd)
    project_file = get_project_file(cwd)
    transcript_path = hook_input.get("transcript_path")

    # Extract context from this session's transcript
    session_context = extract_session_context(transcript_path)

    # Load existing project context
    project_context = load_json(project_file)
    if not project_context:
        project_context = {
            "project_path": cwd,
            "project_name": Path(cwd).name,
            "sessions": [],
            "context": {},
            "cached_content": {},
            "accumulated_files": [],
            "accumulated_commands": []
        }

    # Add this session to project history
    session_record = {
        "session_id": hook_input.get("session_id", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
        "end_time": datetime.now().isoformat(),
        "files_edited": session_context["files_edited"],
        "files_read": session_context["files_read"][:10],
        "commands_count": len(session_context["commands_run"])
    }
    project_context["sessions"].append(session_record)
    project_context["sessions"] = project_context["sessions"][-50:]
    project_context["last_session"] = datetime.now().isoformat()

    # Accumulate frequently used files across sessions
    all_files = set(project_context.get("accumulated_files", []))
    all_files.update(session_context["files_edited"])
    project_context["accumulated_files"] = list(all_files)[-100:]  # Keep last 100

    # Accumulate unique commands
    all_commands = project_context.get("accumulated_commands", [])
    for cmd in session_context["commands_run"]:
        if cmd not in all_commands:
            all_commands.append(cmd)
    project_context["accumulated_commands"] = all_commands[-50:]  # Keep last 50

    # Save project context
    save_json(project_file, project_context)

    # Update global context
    global_context = load_json(GLOBAL_CONTEXT)
    if not global_context:
        global_context = {"all_projects": {}, "global_cache": {}, "session_history": []}

    global_context["all_projects"][project_id] = {
        "path": cwd,
        "name": Path(cwd).name,
        "last_accessed": datetime.now().isoformat(),
        "session_count": len(project_context["sessions"]),
        "total_files_touched": len(project_context.get("accumulated_files", []))
    }

    global_context["session_history"].append({
        "project_id": project_id,
        "project_name": Path(cwd).name,
        "end_time": datetime.now().isoformat(),
        "files_edited": len(session_context["files_edited"]),
        "commands_run": len(session_context["commands_run"])
    })
    global_context["session_history"] = global_context["session_history"][-100:]

    save_json(GLOBAL_CONTEXT, global_context)

    # Summary output
    files_count = len(session_context["files_edited"])
    cmds_count = len(session_context["commands_run"])
    output = {
        "continue": True,
        "message": f"Session saved: {files_count} files edited, {cmds_count} commands | Project: {Path(cwd).name}"
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
