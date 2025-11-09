"""
Multi-Purpose MCP Server for Developer Productivity
Combines all 8 productivity features in one server
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import EmbeddedResource, ImageContent, Resource, TextContent, Tool

# Initialize MCP Server
app = Server("developer-productivity-server")

# ==================== HELPER FUNCTIONS ====================


def run_git_command(command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
    """Execute git commands safely"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_code_file(file_path: str) -> Dict[str, Any]:
    """Analyze a code file for complexity, lines, functions, etc."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        total_lines = len(lines)
        code_lines = len(
            [l for l in lines if l.strip() and not l.strip().startswith("#")]
        )
        comment_lines = len([l for l in lines if l.strip().startswith("#")])

        # Simple function detection
        functions = [l.strip() for l in lines if l.strip().startswith("def ")]
        classes = [l.strip() for l in lines if l.strip().startswith("class ")]

        return {
            "file": file_path,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": total_lines - code_lines - comment_lines,
            "functions": len(functions),
            "classes": len(classes),
            "function_names": [f.split("(")[0].replace("def ", "") for f in functions],
            "class_names": [
                c.split("(")[0].split(":")[0].replace("class ", "") for c in classes
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def generate_documentation(file_path: str, code_analysis: Dict[str, Any]) -> str:
    """Generate documentation for a code file"""
    doc = f"""# Documentation for {os.path.basename(file_path)}

## Overview
- **Total Lines**: {code_analysis.get("total_lines", 0)}
- **Code Lines**: {code_analysis.get("code_lines", 0)}
- **Comment Lines**: {code_analysis.get("comment_lines", 0)}
- **Functions**: {code_analysis.get("functions", 0)}
- **Classes**: {code_analysis.get("classes", 0)}

## Structure

### Classes
"""
    if code_analysis.get("class_names"):
        for cls in code_analysis["class_names"]:
            doc += f"- `{cls}`\n"
    else:
        doc += "- No classes found\n"

    doc += "\n### Functions\n"
    if code_analysis.get("function_names"):
        for func in code_analysis["function_names"]:
            doc += f"- `{func}()`\n"
    else:
        doc += "- No functions found\n"

    return doc


def decompose_task(task_description: str) -> List[Dict[str, Any]]:
    """Decompose a complex task into smaller subtasks"""
    # Simple heuristic-based decomposition
    subtasks = []

    keywords = {
        "create": ["Design", "Implement", "Test", "Document"],
        "build": ["Plan", "Setup", "Develop", "Test", "Deploy"],
        "fix": ["Identify issue", "Debug", "Implement fix", "Test", "Verify"],
        "implement": ["Research", "Design", "Code", "Test", "Review"],
        "add": ["Specify requirements", "Design", "Implement", "Test"],
    }

    task_lower = task_description.lower()
    found_keyword = None

    for keyword, steps in keywords.items():
        if keyword in task_lower:
            found_keyword = keyword
            break

    if found_keyword:
        steps = keywords[found_keyword]
    else:
        steps = ["Plan", "Implement", "Test", "Document"]

    for i, step in enumerate(steps, 1):
        subtasks.append(
            {
                "id": f"subtask-{i}",
                "title": f"{step}: {task_description}",
                "description": f"Step {i} of {len(steps)}",
                "priority": "high" if i == 1 else "medium",
                "estimated_hours": 2 if i <= 2 else 1,
            }
        )

    return subtasks


def estimate_task_time(task_title: str, task_description: str = "") -> Dict[str, Any]:
    """Estimate time required for a task"""
    # Simple estimation based on keywords
    hours = 4  # default

    complexity_indicators = {
        "simple": 2,
        "quick": 1,
        "complex": 8,
        "refactor": 6,
        "bug": 3,
        "feature": 8,
        "ui": 4,
        "api": 5,
        "database": 6,
        "integration": 7,
    }

    text = (task_title + " " + task_description).lower()

    for indicator, est_hours in complexity_indicators.items():
        if indicator in text:
            hours = est_hours
            break

    return {
        "estimated_hours": hours,
        "estimated_days": round(hours / 8, 1),
        "confidence": "medium",
        "complexity": "high" if hours > 6 else "medium" if hours > 3 else "low",
    }


def search_code(query: str, directory: str = ".") -> List[Dict[str, Any]]:
    """Search for code patterns in files"""
    results = []
    try:
        for root, dirs, files in os.walk(directory):
            # Skip common ignored directories
            dirs[:] = [
                d
                for d in dirs
                if d not in [".git", "__pycache__", "node_modules", ".venv", "venv"]
            ]

            for file in files:
                if file.endswith((".py", ".js", ".html", ".css", ".json")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                lines = content.split("\n")
                                matching_lines = [
                                    {"line_number": i + 1, "content": line}
                                    for i, line in enumerate(lines)
                                    if query.lower() in line.lower()
                                ]
                                results.append(
                                    {
                                        "file": file_path,
                                        "matches": len(matching_lines),
                                        "lines": matching_lines[:5],  # First 5 matches
                                    }
                                )
                    except Exception:
                        continue
    except Exception as e:
        return [{"error": str(e)}]

    return results


def generate_tests(file_path: str, functions: List[str]) -> str:
    """Generate basic test templates for functions"""
    test_code = f'''"""
Tests for {os.path.basename(file_path)}
Auto-generated test template
"""

import pytest
from {os.path.splitext(os.path.basename(file_path))[0]} import (
    {", ".join(functions) if functions else "# Import your functions here"}
)

'''

    for func in functions:
        test_code += f'''
def test_{func}():
    """Test {func} function"""
    # Arrange
    # TODO: Setup test data

    # Act
    # result = {func}()

    # Assert
    # assert result is not None
    pass

'''

    return test_code


# ==================== MCP TOOLS ====================


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools"""
    return [
        # 1. Git/GitHub Integration
        Tool(
            name="git_commit_history",
            description="Get recent commit history from the repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to git repository (defaults to current directory)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of commits to retrieve (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="git_status",
            description="Get current git status including changed files",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to git repository",
                    },
                },
            },
        ),
        Tool(
            name="git_contributors",
            description="Get list of contributors and their statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to git repository",
                    },
                },
            },
        ),
        # 2. Code Analysis
        Tool(
            name="analyze_code",
            description="Analyze a code file for complexity, structure, and metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="search_code",
            description="Search for code patterns across the codebase",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or pattern",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in (defaults to current)",
                        "default": ".",
                    },
                },
                "required": ["query"],
            },
        ),
        # 3. Documentation Generation
        Tool(
            name="generate_documentation",
            description="Generate documentation for a code file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file",
                    },
                },
                "required": ["file_path"],
            },
        ),
        # 4. Task Decomposition
        Tool(
            name="decompose_task",
            description="Break down a complex task into smaller subtasks",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Description of the task to decompose",
                    },
                },
                "required": ["task_description"],
            },
        ),
        # 5. Time Estimation
        Tool(
            name="estimate_task_time",
            description="Estimate time required for a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_title": {
                        "type": "string",
                        "description": "Task title",
                    },
                    "task_description": {
                        "type": "string",
                        "description": "Detailed task description",
                        "default": "",
                    },
                },
                "required": ["task_title"],
            },
        ),
        # 6. Test Generation
        Tool(
            name="generate_tests",
            description="Generate test templates for a code file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file",
                    },
                },
                "required": ["file_path"],
            },
        ),
        # 7. Code Review
        Tool(
            name="review_code",
            description="Review code and provide suggestions",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to review",
                    },
                },
                "required": ["file_path"],
            },
        ),
        # 8. Project Statistics
        Tool(
            name="project_statistics",
            description="Get comprehensive project statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Project directory",
                        "default": ".",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool execution"""

    # 1. Git Tools
    if name == "git_commit_history":
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

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"commits": commits, "total": len(commits)}, indent=2
                    ),
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": result.get("error", result.get("stderr"))}, indent=2
                    ),
                )
            ]

    elif name == "git_status":
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
            branch = branch_result["stdout"] if branch_result["success"] else "unknown"

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"branch": branch, "files": files, "total_changes": len(files)},
                        indent=2,
                    ),
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": result.get("error", result.get("stderr"))}, indent=2
                    ),
                )
            ]

    elif name == "git_contributors":
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

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"contributors": contributors, "total": len(contributors)},
                        indent=2,
                    ),
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": result.get("error", result.get("stderr"))}, indent=2
                    ),
                )
            ]

    # 2. Code Analysis
    elif name == "analyze_code":
        file_path = arguments["file_path"]
        analysis = analyze_code_file(file_path)
        return [TextContent(type="text", text=json.dumps(analysis, indent=2))]

    elif name == "search_code":
        query = arguments["query"]
        directory = arguments.get("directory", ".")
        results = search_code(query, directory)
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"query": query, "results": results, "total_matches": len(results)},
                    indent=2,
                ),
            )
        ]

    # 3. Documentation
    elif name == "generate_documentation":
        file_path = arguments["file_path"]
        analysis = analyze_code_file(file_path)
        if "error" not in analysis:
            docs = generate_documentation(file_path, analysis)
            return [TextContent(type="text", text=docs)]
        else:
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]

    # 4. Task Management
    elif name == "decompose_task":
        task_description = arguments["task_description"]
        subtasks = decompose_task(task_description)
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "original_task": task_description,
                        "subtasks": subtasks,
                        "total_subtasks": len(subtasks),
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "estimate_task_time":
        task_title = arguments["task_title"]
        task_description = arguments.get("task_description", "")
        estimation = estimate_task_time(task_title, task_description)
        return [TextContent(type="text", text=json.dumps(estimation, indent=2))]

    # 5. Testing
    elif name == "generate_tests":
        file_path = arguments["file_path"]
        analysis = analyze_code_file(file_path)
        if "error" not in analysis:
            test_code = generate_tests(file_path, analysis.get("function_names", []))
            return [TextContent(type="text", text=test_code)]
        else:
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]

    # 6. Code Review
    elif name == "review_code":
        file_path = arguments["file_path"]
        analysis = analyze_code_file(file_path)

        if "error" not in analysis:
            suggestions = []

            # Check for code quality metrics
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

            review = {
                "file": file_path,
                "metrics": analysis,
                "suggestions": suggestions,
                "overall_score": max(0, 100 - len(suggestions) * 15),
            }

            return [TextContent(type="text", text=json.dumps(review, indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]

    # 7. Project Statistics
    elif name == "project_statistics":
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
                dirs[:] = [
                    d
                    for d in dirs
                    if d not in [".git", "__pycache__", "node_modules", ".venv", "venv"]
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

            return [TextContent(type="text", text=json.dumps(stats, indent=2))]

        except Exception as e:
            return [
                TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))
            ]

    return [
        TextContent(type="text", text=json.dumps({"error": "Unknown tool"}, indent=2))
    ]


@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="git://status",
            name="Git Status",
            mimeType="application/json",
            description="Current git repository status",
        ),
        Resource(
            uri="project://stats",
            name="Project Statistics",
            mimeType="application/json",
            description="Overall project statistics",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource"""
    if uri == "git://status":
        result = run_git_command(["git", "status", "--short"])
        return json.dumps(result, indent=2)
    elif uri == "project://stats":
        # Return basic stats
        return json.dumps(
            {"message": "Use project_statistics tool for detailed stats"}, indent=2
        )
    else:
        return json.dumps({"error": "Resource not found"}, indent=2)


# ==================== SERVER STARTUP ====================


async def main():
    """Start the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
