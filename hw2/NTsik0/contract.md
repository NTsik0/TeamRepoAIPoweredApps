# HW2 · Tool contract · `find_deadlines` · NTsik0

**Tool:** `find_deadlines` · **Owner:** `NTsik0` · **Team repo:** https://github.com/NTsik0/TeamRepoAIPoweredApps (team Make Sense?)

**Code on `main`:** contract class `FindDeadlines` in [`src/contracts.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/src/contracts.py#L52) line 52 · function in [`src/tools.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/src/tools.py#L113) line 113 · registry entry in [`src/tools.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/src/tools.py#L198) line 198 (`TOOLS`) · MCP registration in [`src/mcp_server.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/src/mcp_server.py#L56) line 56

**Product pull request:** [#18](https://github.com/NTsik0/TeamRepoAIPoweredApps/pull/18) · merged commit `5135de6` · golden cases in [`evals/tools/NTsik0.yaml`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/evals/tools/NTsik0.yaml), tool tests in [`tests/test_find_deadlines.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/tests/test_find_deadlines.py)

**In one sentence, for the model:** List the deadlines in a course document, each quoted word for word with the section it comes from. Reads only.

| | |
|---|---|
| **Effect** | reads. No model call: every quote is copied from the document, so a date cannot be invented |
| **Undo** | nothing to undo: no state changes |
| **Idempotent?** | yes. Called twice with `course="cs6920", about="HW2"`, the second result is identical to the first: `{"course": "cs6920", "deadlines": [{"section": "Homework", "quote": "HW2 \"Tool Contract\" is worth 5 points, is released with the Week 5 lab and is due at the end of Week 7."}], "total": 1}`. Nothing is written, so a loop can repeat it safely |
| **Offered to** | everyone, visitors included. It needs no identity, so offering it widely costs nothing |
| **Identity from** | not needed. An identity field sent in the arguments is still refused (`extra="forbid"`), not ignored |
| **Touches** | `data/courses/cs6920.md`, read only, through `load_course()`. No other file, no network |
| **Must never** | state a deadline that is not in the document, or build a file path from the model's text |

**Read or consequential (Lab 7).** `find_deadlines` is a read tool: it changes nothing and returns the same quotes however often it is called, so a loop may run it without asking anyone. In our Lab 7 loop ([`src/agent.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/src/agent.py)) it is the step that checks the deadline in the document; the consequential step, `save_reminder`, is the one parked until the student confirms ([`docs/agent-contract.md`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/docs/agent-contract.md), line 3).

**Inputs.** Unknown fields are refused (`extra="forbid"`).

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `course` | string | one of `cs6920` | The course the deadline belongs to |
| `about` | string or null | pattern `^[A-Za-z0-9][A-Za-z0-9 -]{1,29}$`, default null | Only deadlines that mention this word, e.g. HW2 or Demo Day |
| `limit` | integer | 1 to 20, default 10 | The most deadlines to return |

**Result.** `course`, `deadlines` (list of `section`, `quote`), `total` (matches before the limit). No file paths, no internal ids.

**Expected failures**

| When | Message the model reads (what happened, what to do next) |
|---|---|
| nothing matches `about` | No deadline in the cs6920 document mentions '<about>'. Try a shorter word, like HW2, or leave 'about' out to list every deadline. |

**Tests and golden cases**

| Case | Expect | Where |
|---|---|---|
| a valid call (all deadlines) | runs, `total: 4`, every quote is in the document | `evals/tools/NTsik0.yaml` n1 · `test_every_quote_is_copied_from_the_document` |
| invalid arguments (`limit: 500`) | refused before the tool runs | b1 |
| not offered to this caller | n/a: offered to everyone because it only reads; `test_it_is_offered_to_visitors_because_it_only_reads` | `tests/test_find_deadlines.py` |
| identity in the arguments (`student: s999`) | refused | a3 |
| adversarial: `course: "../../.env"` | refused | a1 |
| adversarial: instructions in `about` | refused | a2 |

**Log line.** `logs/tools.jsonl`: timestamp (UTC), tool, raw arguments, ok, error, latency, and the caller only as a 12-character hash (null for a visitor). It never contains the student id or the question text.

**Known limit.** It quotes the document as written. `data/courses/cs6920.md` still says HW1 was due "Thursday of Week 4"; the extension is in `data/corpus/milestones/hw1.md`, which this tool does not read.

**The decision I had to make.** The function I wrapped does the job of my HW1 Deadline Finder ([`hw1/NTsik0/src/deadlines.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/hw1/NTsik0/src/deadlines.py)), which sent the deadline sections to the model, asked it to list the deadlines, and then dropped any it could not find word for word. As a tool, `find_deadlines` cannot call a model at all: it splits each section into sentences and returns the ones that state a deadline, copied. I removed the model because the tool's caller is already a model; a second model inside the tool would cost a call per lookup, could reword a date, and could be steered by text in the document, while copying cannot invent anything. I also narrowed `course` from any id (HW1's `load_sections(course_id: str)`) to `Literal["cs6920"]`, so the model's text never reaches a file name. Both are visible in the code: the docstring of `find_deadlines` in `src/tools.py` line 113 ("No model: the quotes are copied from the document, so a date cannot be invented") and `CourseId` in `src/contracts.py` line 20, and in the plan recorded in delegation log entry 5 ("read-only, no model call").
