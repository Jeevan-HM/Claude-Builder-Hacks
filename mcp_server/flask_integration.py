"""
Flask Integration for MCP Server
Provides REST API endpoints to interact with MCP tools
"""

import json
import os
from typing import Any

from flask import Blueprint, jsonify, request

# Import MCP functions directly
from mcp_server.server import (
    analyze_code_file,
    decompose_task,
    estimate_task_time,
    generate_documentation,
    generate_tests,
    run_git_command,
    search_code,
)

# Create Blueprint
mcp_bp = Blueprint("mcp", __name__, url_prefix="/api/mcp")


def call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call an MCP tool directly"""
    try:
        # Call the appropriate function based on tool name
        if tool_name == "git_commit_history":
            repo_path = arguments.get("repo_path", ".")
            limit = arguments.get("limit", 10)
            result = run_git_command(
                ["git", "log", f"-{limit}", "--pretty=format:%H|%an|%ae|%ad|%s"],
                cwd=repo_path,
            )
            if result["success"]:
                commits = []
                for line in result["stdout"].split("\n"):
                    if line:
                        parts = line.split("|")
                        if len(parts) == 5:
                            commits.append(
                                {
                                    "hash": parts[0][:8],
                                    "author": parts[1],
                                    "email": parts[2],
                                    "date": parts[3],
                                    "message": parts[4],
                                }
                            )
                return {"commits": commits, "total": len(commits)}
            return {"error": result.get("stderr", "Unknown error")}

        elif tool_name == "git_status":
            repo_path = arguments.get("repo_path", ".")
            result = run_git_command(["git", "status", "--short"], cwd=repo_path)
            if result["success"]:
                files = []
                for line in result["stdout"].split("\n"):
                    if line:
                        status = line[:2].strip()
                        file_path = line[3:].strip()
                        files.append({"status": status, "file": file_path})
                branch_result = run_git_command(
                    ["git", "branch", "--show-current"], cwd=repo_path
                )
                branch = (
                    branch_result["stdout"] if branch_result["success"] else "unknown"
                )
                return {"branch": branch, "files": files, "total_changes": len(files)}
            return {"error": result.get("stderr", "Unknown error")}

        elif tool_name == "analyze_code":
            file_path = arguments.get("file_path")
            return analyze_code_file(file_path)

        elif tool_name == "search_code":
            query = arguments.get("query")
            directory = arguments.get("directory", ".")
            results = search_code(query, directory)
            return {"query": query, "results": results, "total_matches": len(results)}

        elif tool_name == "generate_documentation":
            file_path = arguments.get("file_path")
            analysis = analyze_code_file(file_path)
            if "error" not in analysis:
                docs = generate_documentation(file_path, analysis)
                return {"documentation": docs, "file": file_path}
            return analysis

        elif tool_name == "decompose_task":
            task_description = arguments.get("task_description")
            subtasks = decompose_task(task_description)
            return {
                "original_task": task_description,
                "subtasks": subtasks,
                "total_subtasks": len(subtasks),
            }

        elif tool_name == "estimate_task_time":
            task_title = arguments.get("task_title")
            task_description = arguments.get("task_description", "")
            return estimate_task_time(task_title, task_description)

        elif tool_name == "generate_tests":
            file_path = arguments.get("file_path")
            analysis = analyze_code_file(file_path)
            if "error" not in analysis:
                test_code = generate_tests(
                    file_path, analysis.get("function_names", [])
                )
                return {"test_code": test_code, "file": file_path}
            return analysis

        elif tool_name == "review_code":
            file_path = arguments.get("file_path")
            analysis = analyze_code_file(file_path)
            if "error" not in analysis:
                suggestions = []
                if analysis["comment_lines"] < analysis["code_lines"] * 0.1:
                    suggestions.append(
                        {
                            "severity": "medium",
                            "message": "Consider adding more comments (less than 10% comment coverage)",
                        }
                    )
                if analysis["functions"] == 0 and analysis["code_lines"] > 50:
                    suggestions.append(
                        {
                            "severity": "high",
                            "message": "Consider refactoring into functions for better modularity",
                        }
                    )
                if analysis["code_lines"] > 500:
                    suggestions.append(
                        {
                            "severity": "medium",
                            "message": "File is large (500+ lines). Consider splitting into smaller modules",
                        }
                    )
                return {
                    "file": file_path,
                    "metrics": analysis,
                    "suggestions": suggestions,
                    "overall_score": max(0, 100 - len(suggestions) * 15),
                }
            return analysis

        elif tool_name == "git_contributors":
            repo_path = arguments.get("repo_path", ".")
            result = run_git_command(
                ["git", "shortlog", "-sn", "--all"],
                cwd=repo_path,
            )
            if result["success"]:
                contributors = []
                for line in result["stdout"].split("\n"):
                    if line:
                        parts = line.strip().split("\t")
                        if len(parts) == 2:
                            contributors.append(
                                {"commits": int(parts[0]), "name": parts[1]}
                            )
                return {"contributors": contributors, "total": len(contributors)}
            return {"error": result.get("stderr", "Unknown error")}

        elif tool_name == "project_statistics":
            directory = arguments.get("directory", ".")

            stats = {
                "total_files": 0,
                "total_lines": 0,
                "total_code_lines": 0,
                "languages": {},
                "largest_files": [],
            }

            files_data = []

            try:
                for root, dirs, files in os.walk(directory):
                    # Skip common directories
                    dirs[:] = [
                        d
                        for d in dirs
                        if d
                        not in [".git", "__pycache__", "node_modules", ".venv", "venv"]
                    ]

                    for file in files:
                        if file.endswith((".py", ".js", ".html", ".css", ".json")):
                            file_path = os.path.join(root, file)
                            ext = os.path.splitext(file)[1]

                            try:
                                analysis = analyze_code_file(file_path)
                                if "error" not in analysis:
                                    stats["total_files"] += 1
                                    stats["total_lines"] += analysis["total_lines"]
                                    stats["total_code_lines"] += analysis["code_lines"]

                                    stats["languages"][ext] = (
                                        stats["languages"].get(ext, 0) + 1
                                    )

                                    files_data.append(
                                        {
                                            "file": file_path,
                                            "lines": analysis["total_lines"],
                                        }
                                    )
                            except Exception:
                                continue

                # Get largest files
                files_data.sort(key=lambda x: x["lines"], reverse=True)
                stats["largest_files"] = files_data[:5]

                return stats

            except Exception as e:
                return {"error": str(e)}

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"error": str(e)}


# ==================== API ENDPOINTS ====================


@mcp_bp.route("/tools", methods=["GET"])
def list_tools():
    """List all available MCP tools"""
    tools = [
        {
            "name": "git_commit_history",
            "description": "Get recent commit history",
            "category": "git",
        },
        {"name": "git_status", "description": "Get git status", "category": "git"},
        {
            "name": "git_contributors",
            "description": "Get contributors list",
            "category": "git",
        },
        {
            "name": "analyze_code",
            "description": "Analyze code metrics",
            "category": "code_analysis",
        },
        {
            "name": "search_code",
            "description": "Search code patterns",
            "category": "code_analysis",
        },
        {
            "name": "generate_documentation",
            "description": "Generate documentation",
            "category": "documentation",
        },
        {
            "name": "decompose_task",
            "description": "Break down tasks",
            "category": "task_management",
        },
        {
            "name": "estimate_task_time",
            "description": "Estimate task duration",
            "category": "task_management",
        },
        {
            "name": "generate_tests",
            "description": "Generate test templates",
            "category": "testing",
        },
        {
            "name": "review_code",
            "description": "Review code quality",
            "category": "code_review",
        },
        {
            "name": "project_statistics",
            "description": "Get project stats",
            "category": "analytics",
        },
    ]
    return jsonify({"tools": tools, "total": len(tools)})


@mcp_bp.route("/git/commits", methods=["GET"])
def get_commits():
    """Get git commit history"""
    limit = request.args.get("limit", 10, type=int)
    repo_path = request.args.get("repo_path", ".")

    result = call_mcp_tool(
        "git_commit_history", {"repo_path": repo_path, "limit": limit}
    )
    return jsonify(result)


@mcp_bp.route("/git/status", methods=["GET"])
def get_git_status():
    """Get git status"""
    repo_path = request.args.get("repo_path", ".")
    result = call_mcp_tool("git_status", {"repo_path": repo_path})
    return jsonify(result)


@mcp_bp.route("/git/contributors", methods=["GET"])
def get_contributors():
    """Get git contributors"""
    repo_path = request.args.get("repo_path", ".")
    result = call_mcp_tool("git_contributors", {"repo_path": repo_path})
    return jsonify(result)


@mcp_bp.route("/code/analyze", methods=["POST"])
def analyze_code():
    """Analyze a code file"""
    data = request.json
    file_path = data.get("file_path")

    if not file_path:
        return jsonify({"error": "file_path is required"}), 400

    result = call_mcp_tool("analyze_code", {"file_path": file_path})
    return jsonify(result)


@mcp_bp.route("/code/search", methods=["POST"])
def search_code():
    """Search code patterns"""
    data = request.json
    query = data.get("query")
    directory = data.get("directory", ".")

    if not query:
        return jsonify({"error": "query is required"}), 400

    result = call_mcp_tool("search_code", {"query": query, "directory": directory})
    return jsonify(result)


@mcp_bp.route("/docs/generate", methods=["POST"])
def generate_docs():
    """Generate documentation"""
    data = request.json
    file_path = data.get("file_path")

    if not file_path:
        return jsonify({"error": "file_path is required"}), 400

    result = call_mcp_tool("generate_documentation", {"file_path": file_path})
    return jsonify(result)


@mcp_bp.route("/tasks/decompose", methods=["POST"])
def decompose_task():
    """Decompose a task into subtasks"""
    data = request.json
    task_description = data.get("task_description")

    if not task_description:
        return jsonify({"error": "task_description is required"}), 400

    result = call_mcp_tool("decompose_task", {"task_description": task_description})
    return jsonify(result)


@mcp_bp.route("/tasks/estimate", methods=["POST"])
def estimate_task():
    """Estimate task time"""
    data = request.json
    task_title = data.get("task_title")
    task_description = data.get("task_description", "")

    if not task_title:
        return jsonify({"error": "task_title is required"}), 400

    result = call_mcp_tool(
        "estimate_task_time",
        {"task_title": task_title, "task_description": task_description},
    )
    return jsonify(result)


@mcp_bp.route("/tests/generate", methods=["POST"])
def generate_tests():
    """Generate test templates"""
    data = request.json
    file_path = data.get("file_path")

    if not file_path:
        return jsonify({"error": "file_path is required"}), 400

    result = call_mcp_tool("generate_tests", {"file_path": file_path})
    return jsonify(result)


@mcp_bp.route("/code/review", methods=["POST"])
def review_code():
    """Review code quality"""
    data = request.json
    file_path = data.get("file_path")

    if not file_path:
        return jsonify({"error": "file_path is required"}), 400

    result = call_mcp_tool("review_code", {"file_path": file_path})
    return jsonify(result)


@mcp_bp.route("/project/stats", methods=["GET"])
def project_stats():
    """Get project statistics"""
    directory = request.args.get("directory", ".")
    result = call_mcp_tool("project_statistics", {"directory": directory})
    return jsonify(result)


@mcp_bp.route("/call_tool", methods=["POST"])
def call_tool_endpoint():
    """Generic endpoint to call any MCP tool"""
    data = request.json
    tool_name = data.get("toolName")
    props = data.get("props", {})

    if not tool_name:
        return jsonify({"error": "toolName is required"}), 400

    result = call_mcp_tool(tool_name, props)

    # Wrap the result in the expected format
    response_data = {"contents": [{"text": json.dumps(result), "type": "text"}]}

    return jsonify(response_data)


@mcp_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "mcp-integration"})
