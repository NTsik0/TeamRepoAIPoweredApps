"""The tool contracts: what each capability accepts, as types the code can check (Week 5).

This file is the single source of truth for tool inputs. Two doors read it:
  * src/tools.py builds the function-calling schema the model sees (the Args models below)
  * src/mcp_server.py builds the MCP tool from the same type aliases
tests/test_mcp.py fails if the two doors ever describe a tool differently.

Rules that hold for every contract (docs/tool-contracts.md):
  * extra="forbid": an argument we did not ask for is an error, never ignored
  * every string has a pattern or a fixed set of values; every number has bounds
  * nothing here names WHO is calling. Identity comes from the server, never the model.
"""
from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

CourseId = Annotated[Literal["cs6920"], Field(description="The course the deadline belongs to")]
Title = Annotated[str, Field(
    pattern=r"^[A-Za-z0-9][A-Za-z0-9 .,:()'&/-]{2,79}$",
    description="What is due, as named in the course document, e.g. HW2 Tool Contract")]
DueDate = Annotated[date, Field(description="The due date, as written in the course document, YYYY-MM-DD")]
DaysBefore = Annotated[int, Field(ge=1, le=7, description="Remind this many days before the due date, 1 to 7")]
Keyword = Annotated[str, Field(
    pattern=r"^[A-Za-z0-9][A-Za-z0-9 -]{1,29}$",
    description="Only deadlines that mention this word, e.g. HW2 or Demo Day: 2 to 30 letters, digits, spaces or hyphens")]
Limit = Annotated[int, Field(ge=1, le=20, description="The most deadlines to return, 1 to 20")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SaveReminder(Contract):
    """Save a reminder for one course deadline for the signed-in student. Adds only: it never removes, changes or sends anything."""
    course: CourseId
    title: Title
    due: DueDate
    days_before: DaysBefore = 2


class FindDeadlines(Contract):
    """List the deadlines in a course document, each quoted word for word with the section it comes from. Reads only."""
    course: CourseId
    about: Keyword | None = None
    limit: Limit = 10
