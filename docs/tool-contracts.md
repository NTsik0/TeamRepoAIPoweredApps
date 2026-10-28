# Tool contracts · KIU CourseMate

*Filled from `Lab-5/templates/tool-contract.md`. Every rule below exists in code: the contract class in `src/contracts.py`, the tool body in `src/tools.py`, or the registry and gates in `src/tools.py` and `src/act.py`.*

## `save_reminder`

**In one sentence, for the model:** Save a reminder for one course deadline for the signed-in student. Adds only: it never removes, changes or sends anything.

| | |
|---|---|
| **Effect** | adds |
| **Undo** | the student deletes the reminder in the app (a button, not a tool; not built yet) |
| **Idempotent?** | yes: the same course, title and due date a second time returns `already saved` and changes nothing |
| **Offered to** | signed-in students only. A visitor (`tools_for(None)`) is never offered it |
| **Identity from** | the request: the `X-Student-Id` header on `POST /act` (stand-in for real sign-in, Week 12); `Resolve(signed_in_student)` from `COURSEMATE_STUDENT` in the MCP server. Never an argument |
| **Touches** | one file, `$COURSEMATE_STATE_DIR/reminders.json` (default `state/reminders.json`), storing a hash of the student id, never the id |
| **Must never** | save a reminder for anyone but the caller; delete or edit a reminder; send a message or e-mail |

**Inputs.** Unknown fields are refused (`extra="forbid"`).

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `course` | string | one of `cs6920` | The course the deadline belongs to |
| `title` | string | pattern `^[A-Za-z0-9][A-Za-z0-9 .,:()'&/-]{2,79}$` (3 to 80 characters, letters, digits, basic punctuation; no `<`, `;`, quotes or newlines) | What is due, as named in the course document, e.g. HW2 Tool Contract |
| `due` | date | a real calendar date, `YYYY-MM-DD` | The due date, as written in the course document |
| `days_before` | integer | 1 to 7, default 2 | Remind this many days before the due date |

**Result.** `course`, `title`, `due` (date), `remind_on` (date: `due − days_before`, or today if that has passed), `status` (`saved` or `already saved`), `reminders` (how many this student now has).

**Expected failures.** Each raises `ToolFailure`; the message goes back to the model.

| When | Message the model reads (what happened, what to do next) |
|---|---|
| `due` is before today | That deadline (YYYY-MM-DD) has already passed. Ask the student for the right date from the course document. |
| `due` is more than 180 days ahead | YYYY-MM-DD is more than 180 days away, outside this semester. Check the date in the course document. |
| the student already has 50 reminders | You already have 50 saved reminders, the most allowed. Nothing was saved. |

**Tests and golden cases**

| Case | Expect | Where |
|---|---|---|
| a valid call | runs, `status: saved`, `remind_on` two days before | `tests/test_act.py::test_valid_call_runs_and_saves` |
| invalid arguments (`title: "<script>"`) | refused before the tool runs | `test_invalid_arguments_never_reach_the_tool` |
| not offered to a visitor | refused, nothing runs | `test_a_tool_not_offered_is_not_run` |
| identity in the arguments (`student: "s999"`) | refused | `test_model_cannot_choose_the_student` |
| both doors (function calling and MCP) | same schema | `tests/test_mcp.py` |

**Log line.** `logs/tools.jsonl`, one line per call: timestamp (UTC), tool, the raw arguments, ok, the error, a 12-character hash of the student id, latency. It leaves out the student id itself and never contains the question text.

## HW2 owners

Each member wraps a different capstone function for HW2. Neither is `save_reminder`, the team's Lab 5 tool.

| Member | Function for HW2 | Effect |
|---|---|---|
| Nikoloz Tsikaridze (NTsik0) | `find_deadlines`: every deadline in a course document, quoted word for word with its section | reads |
| Guram Tsiklauri (Gaaa-3) | `search_course_docs`: the top sections for a question, with citations | reads |
