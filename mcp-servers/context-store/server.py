#!/usr/bin/env python3
"""
Context Store MCP Server - Persistent context storage across sessions.
Supports: per-project context, cross-folder access, multi-session
Fixed: Proper MCP protocol initialization
"""

import json
import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime

STORE_DIR = Path.home() / ".claude" / ".session_store"
PROJECTS_DIR = STORE_DIR / "projects"
GLOBAL_CONTEXT = STORE_DIR / "global_context.json"
CACHE_FILE = STORE_DIR / "permanent_cache.json"
PLANS_CACHE = STORE_DIR / "cached_plans.json"

STORE_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

def get_project_id(path):
    return hashlib.md5(path.encode()).hexdigest()[:12]

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

class ContextStoreMCP:
    def __init__(self):
        self.cwd = os.getcwd()
        self.project_id = get_project_id(self.cwd)
        self.initialized = False
        self.tools = {
            "store_project_context": self.store_project_context,
            "get_project_context": self.get_project_context,
            "list_all_projects": self.list_all_projects,
            "get_other_project_context": self.get_other_project_context,
            "store_global": self.store_global,
            "get_global": self.get_global,
            "cache_plan": self.cache_plan,
            "get_cached_plan": self.get_cached_plan,
            "list_cached_plans": self.list_cached_plans,
            "store_priority_content": self.store_priority_content,
            "get_priority_content": self.get_priority_content,
            "get_session_history": self.get_session_history,
            "get_project_sessions": self.get_project_sessions,
        }

    def _get_project_file(self, project_id=None):
        pid = project_id or self.project_id
        return PROJECTS_DIR / f"{pid}.json"

    def _load_project(self, project_id=None):
        return load_json(self._get_project_file(project_id))

    def _save_project(self, data, project_id=None):
        save_json(self._get_project_file(project_id), data)

    def store_project_context(self, key: str, value: str, priority: int = 5) -> str:
        project = self._load_project()
        if "context" not in project:
            project["context"] = {}
        project["context"][key] = {
            "value": value,
            "priority": priority,
            "stored_at": datetime.now().isoformat()
        }
        self._save_project(project)
        return f"Stored '{key}' in project {Path(self.cwd).name} (priority {priority})"

    def get_project_context(self, key: str = None) -> str:
        project = self._load_project()
        ctx = project.get("context", {})
        if key:
            return ctx.get(key, {}).get("value", f"Not found: {key}")
        if not ctx:
            return "No project context stored"
        return "\n".join([f"[{k}]: {v['value'][:100]}..." for k, v in ctx.items()])

    def list_all_projects(self) -> str:
        global_ctx = load_json(GLOBAL_CONTEXT)
        projects = global_ctx.get("all_projects", {})
        if not projects:
            return "No projects tracked yet"
        result = ["Known Projects:"]
        for pid, info in projects.items():
            result.append(f"  [{pid}] {info['name']} - {info['path']} ({info['session_count']} sessions)")
        return "\n".join(result)

    def get_other_project_context(self, project_id: str, key: str = None) -> str:
        project = self._load_project(project_id)
        if not project:
            return f"Project {project_id} not found"
        ctx = project.get("context", {})
        if key:
            return ctx.get(key, {}).get("value", f"Key '{key}' not found in project {project_id}")
        if not ctx:
            return f"No context in project {project_id}"
        return "\n".join([f"[{k}]: {v['value'][:100]}..." for k, v in ctx.items()])

    def store_global(self, key: str, value: str) -> str:
        global_ctx = load_json(GLOBAL_CONTEXT)
        if "global_cache" not in global_ctx:
            global_ctx["global_cache"] = {}
        global_ctx["global_cache"][key] = {
            "value": value,
            "stored_at": datetime.now().isoformat()
        }
        save_json(GLOBAL_CONTEXT, global_ctx)
        return f"Stored '{key}' in global cache (available everywhere)"

    def get_global(self, key: str = None) -> str:
        global_ctx = load_json(GLOBAL_CONTEXT)
        cache = global_ctx.get("global_cache", {})
        if key:
            return cache.get(key, {}).get("value", f"Global key not found: {key}")
        if not cache:
            return "No global cache"
        return "\n".join([f"[{k}]: {v['value'][:100]}..." for k, v in cache.items()])

    def cache_plan(self, plan_name: str, content: str) -> str:
        data = load_json(PLANS_CACHE)
        data[plan_name] = {
            "content": content,
            "cached_at": datetime.now().isoformat(),
            "size_chars": len(content)
        }
        save_json(PLANS_CACHE, data)
        return f"Cached plan '{plan_name}' ({len(content):,} chars)"

    def get_cached_plan(self, plan_name: str) -> str:
        data = load_json(PLANS_CACHE)
        return data.get(plan_name, {}).get("content", f"Plan not found: {plan_name}")

    def list_cached_plans(self) -> str:
        data = load_json(PLANS_CACHE)
        if not data:
            return "No cached plans"
        return "\n".join([f"- {n}: {i['size_chars']:,} chars" for n, i in data.items()])

    def store_priority_content(self, content_id: str, content: str, description: str = "") -> str:
        data = load_json(CACHE_FILE)
        data[content_id] = {
            "content": content,
            "description": description,
            "priority": 10,
            "stored_at": datetime.now().isoformat(),
            "size_chars": len(content)
        }
        save_json(CACHE_FILE, data)
        return f"Stored priority '{content_id}' ({len(content):,} chars) - NEVER deleted"

    def get_priority_content(self, content_id: str = None) -> str:
        data = load_json(CACHE_FILE)
        if content_id:
            return data.get(content_id, {}).get("content", f"Not found: {content_id}")
        if not data:
            return "No priority content"
        return "\n".join([f"- {k}: {v.get('description', '')} ({v['size_chars']:,} chars)" for k, v in data.items()])

    def get_session_history(self, limit: int = 20) -> str:
        global_ctx = load_json(GLOBAL_CONTEXT)
        sessions = global_ctx.get("session_history", [])[-limit:]
        if not sessions:
            return "No session history"
        return "\n".join([f"- {s['end_time']}: {s['project_name']}" for s in sessions])

    def get_project_sessions(self, project_id: str = None) -> str:
        project = self._load_project(project_id)
        sessions = project.get("sessions", [])
        if not sessions:
            return "No sessions for this project"
        return f"Project: {project.get('project_name', 'unknown')}\n" + \
               "\n".join([f"- {s['end_time']}" for s in sessions[-20:]])

    def get_tools_list(self):
        return [
            {"name": "store_project_context", "description": "Store context for current project",
             "inputSchema": {"type": "object", "properties": {"key": {"type": "string", "description": "Key name"}, "value": {"type": "string", "description": "Value to store"}, "priority": {"type": "integer", "default": 5}}, "required": ["key", "value"]}},
            {"name": "get_project_context", "description": "Get context from current project",
             "inputSchema": {"type": "object", "properties": {"key": {"type": "string", "description": "Optional key to retrieve"}}}},
            {"name": "list_all_projects", "description": "List all known projects",
             "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_other_project_context", "description": "Get context from another project",
             "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string"}, "key": {"type": "string"}}, "required": ["project_id"]}},
            {"name": "store_global", "description": "Store in global cache (available everywhere)",
             "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}, "required": ["key", "value"]}},
            {"name": "get_global", "description": "Get from global cache",
             "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}}}},
            {"name": "cache_plan", "description": "Cache a development plan",
             "inputSchema": {"type": "object", "properties": {"plan_name": {"type": "string"}, "content": {"type": "string"}}, "required": ["plan_name", "content"]}},
            {"name": "get_cached_plan", "description": "Get a cached plan",
             "inputSchema": {"type": "object", "properties": {"plan_name": {"type": "string"}}, "required": ["plan_name"]}},
            {"name": "list_cached_plans", "description": "List all cached plans",
             "inputSchema": {"type": "object", "properties": {}}},
            {"name": "store_priority_content", "description": "Store priority content (never deleted)",
             "inputSchema": {"type": "object", "properties": {"content_id": {"type": "string"}, "content": {"type": "string"}, "description": {"type": "string"}}, "required": ["content_id", "content"]}},
            {"name": "get_priority_content", "description": "Get priority content",
             "inputSchema": {"type": "object", "properties": {"content_id": {"type": "string"}}}},
            {"name": "get_session_history", "description": "Get global session history",
             "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "default": 20}}}},
            {"name": "get_project_sessions", "description": "Get sessions for a project",
             "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string"}}}}
        ]

    def handle_request(self, request):
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        # MCP Protocol: Initialize
        if method == "initialize":
            self.initialized = True
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "context-store",
                    "version": "1.0.0"
                }
            }

        # MCP Protocol: Initialized notification
        if method == "notifications/initialized":
            return None  # No response needed for notifications

        # MCP Protocol: List tools
        if method == "tools/list":
            return {"tools": self.get_tools_list()}

        # MCP Protocol: Call tool
        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name](**arguments)
                    return {"content": [{"type": "text", "text": str(result)}]}
                except Exception as e:
                    return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}
            return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}

        # Unknown method
        return {"error": {"code": -32601, "message": f"Method not found: {method}"}}

    def run(self):
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                    
                request = json.loads(line)
                response = self.handle_request(request)
                
                # Skip response for notifications
                if response is None:
                    continue
                    
                response["jsonrpc"] = "2.0"
                if "id" in request:
                    response["id"] = request["id"]
                    
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                sys.stderr.write(f"JSON decode error: {e}\n")
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")
                continue

if __name__ == "__main__":
    ContextStoreMCP().run()
