"""CourseMate as an MCP server: the same tool, now usable by any MCP host (Week 5).

Run it over stdio (what Claude Code, Cursor and VS Code launch):
    COURSEMATE_STUDENT=s123 python -m src.mcp_server
Connect Claude Code from the repo root:
    claude mcp add --env COURSEMATE_STUDENT=test-student --transport stdio coursemate -- python -m src.mcp_server

MCP Python SDK 2.x (MCPServer, formerly FastMCP). The schema of every tool comes from the type
hints, which come from src/contracts.py. tests/test_mcp.py checks both doors stay identical.
"""
from __future__ import annotations

import os
import sys
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver import Resolve
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from src import tools
from src.contracts import CourseId, DaysBefore, DueDate, SaveReminder, Title

mcp = MCPServer("coursemate", instructions="KIU CS6920 course assistant: save reminders for course deadlines.")
ADDS = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)


def signed_in_student() -> str:
    """Who is calling. Set by whoever launches the server, never by the model."""
    student = os.environ.get("COURSEMATE_STUDENT")
    if not student:
        raise ToolError("Not signed in: this server was started without COURSEMATE_STUDENT.")
    return student


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except tools.ToolFailure as e:          # expected failures reach the model as readable errors
        raise ToolError(str(e)) from e


@mcp.tool(annotations=ADDS, description=SaveReminder.__doc__)
def save_reminder(course: CourseId, title: Title, due: DueDate,
                  student: Annotated[str, Resolve(signed_in_student)],
                  days_before: DaysBefore = 2) -> tools.ReminderResult:
    return _run(tools.save_reminder,
                SaveReminder(course=course, title=title, due=due, days_before=days_before), student=student)


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run("streamable-http", host="127.0.0.1", port=8000)
    else:
        mcp.run()
