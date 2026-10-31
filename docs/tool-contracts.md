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

## `find_deadlines` · HW2 · NTsik0

**In one sentence, for the model:** List the deadlines in a course document, each quoted word for word with the section it comes from. Reads only.

| | |
|---|---|
| **Effect** | reads |
| **Undo** | nothing to undo |
| **Idempotent?** | yes: it changes nothing |
| **Offered to** | everyone, including visitors who are not signed in |
| **Identity from** | not needed: the answer is the same for every caller. An identity field in the arguments is still refused (`extra="forbid"`) |
| **Touches** | `data/courses/cs6920.md`, read only, through `load_course()` |
| **Must never** | state a deadline that is not in the document, or read any other file |

**Inputs.** Unknown fields are refused (`extra="forbid"`).

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `course` | string | one of `cs6920` | The course the deadline belongs to |
| `about` | string or null | pattern `^[A-Za-z0-9][A-Za-z0-9 -]{1,29}$` (2 to 30 letters, digits, spaces, hyphens), default null | Only deadlines that mention this word, e.g. HW2 or Demo Day |
| `limit` | integer | 1 to 20, default 10 | The most deadlines to return |

**Result.** `course`, `deadlines` (list of `section`, `quote`), `total` (matches before the limit). No file paths.

**Expected failures**

| When | Message the model reads |
|---|---|
| nothing matches `about` | No deadline in the cs6920 document mentions '<about>'. Try a shorter word, like HW2, or leave 'about' out to list every deadline. |

**Known limit.** It quotes the document as written. `data/courses/cs6920.md` still says HW1 was due "Thursday of Week 4"; the extension is in `data/corpus/milestones/hw1.md`, which this tool does not read.

**Tests and golden cases:** `evals/tools/NTsik0.yaml` (7 cases: 3 normal, 1 bad input, 3 adversarial) and `tests/test_find_deadlines.py`.

**Log line.** Same as every tool: `logs/tools.jsonl`, no student id (a visitor has none; a signed-in caller is logged as a hash).

## `search_course_docs` · HW2 · Gaaa-3

**In one sentence, for the model:** Find the sections of the course documents that answer a question, each with the document it came from. Reads only.

| | |
|---|---|
| **Effect** | reads. No model call: the Week 4 retriever ranks the sections and the text is copied from the document |
| **Undo** | nothing to undo |
| **Idempotent?** | yes: the same question returns the same sections and changes nothing |
| **Offered to** | everyone, including visitors who are not signed in |
| **Identity from** | not needed: the course documents are the same for every student. An identity field in the arguments is still refused (`extra="forbid"`) |
| **Touches** | `data/corpus/` (12 documents), read only, through `load_corpus()`; `data/index/` is read if it exists and built in memory if it does not. The built index is cached for the life of the process: a rebuilt index or a changed corpus needs a restart to be seen |
| **Must never** | return text that is not in a course document, name a file path, or treat the question or the documents as instructions |

**Inputs.** Unknown fields are refused (`extra="forbid"`).

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `course` | string | one of `cs6920` | The course whose documents to search |
| `question` | string | pattern `^[A-Za-z0-9][A-Za-z0-9 ?.,'()/%-]{2,199}$` (3 to 200 characters; letters, digits, spaces and `? . , ' ( ) / % -`; no `:`, `#`, `<`, quotes or newlines) | The question to look up, in the words the course uses, e.g. How many points is the Design Review worth? |
| `k` | integer | 1 to 5, default 3 | The most sections to return |

**Result.** `course`, `sources` (the distinct documents behind the sections, in rank order, what a citation line is built from) and `sections` (list of `source`, `heading`, `text`). `source` is a document id such as `milestones/hw1`, never a file path. `text` is the section as written, with line breaks collapsed to spaces and cut at 600 characters at a word boundary.

**Expected failures.** Raises `ToolFailure`; the message goes back to the model.

| When | Message the model reads (what happened, what to do next) |
|---|---|
| nothing retrieved scores above the relevance floor (`min_score()` in `src/answer.py`: 0.15 offline, 0.25 live) | Nothing in the cs6920 course documents matched that question. Ask a shorter question in the words the course uses, like 'Design Review points' or 'HW2 deadline'. |

**Known limits.**

1. The pattern keeps punctuation that fakes a system turn (`:`, `#`) out of the field, but it cannot stop an English imperative written in plain words. What makes that harmless is the effect, not the pattern: the tool only ranks sections of `data/corpus/` and returns them as data, so there is nothing for an instruction to act on.
2. Keeping `:` out also refuses questions that contain a clock time: "Does the Demo Day start at 10:00?" has to be asked as "10 00", or without the time. That is a cost we chose on purpose; `/`, `%`, `(` and `)` were added after review (#22) because they appear in ordinary questions and carry no such risk.
3. The pattern is Latin-only, so a question written in Georgian is refused before the search runs. Today that changes nothing a student could get: every document in `data/corpus/` is in English, so a Georgian question would retrieve nothing useful even if it validated. Widening the pattern is a decision for when the corpus is bilingual, not before.
4. The relevance floor uses the offline embedding model's scale in CI; a short nonsense string can score above it, while an off-topic sentence does not.

**Tests and golden cases:** `evals/tools/Gaaa-3.yaml` (7 cases: 4 normal, 1 bad input, 2 adversarial) and `tests/test_search_course_docs.py`.

**Log line.** Same as every tool: `logs/tools.jsonl`, one line per call, the caller only as a 12-character hash (null for a visitor). The raw arguments are logged, so the question text is in this log; it is a course question, never a name or an id.

## HW2 owners

Each member wraps a different capstone function for HW2. Neither is `save_reminder`, the team's Lab 5 tool.

| Member | Function for HW2 | Effect |
|---|---|---|
| Nikoloz Tsikaridze (NTsik0) | `find_deadlines`: every deadline in a course document, quoted word for word with its section | reads |
| Guram Tsiklauri (Gaaa-3) | `search_course_docs`: the top sections for a question, with citations | reads |
