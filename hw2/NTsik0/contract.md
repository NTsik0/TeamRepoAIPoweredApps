# HW2 · Tool contract · `find_deadlines` · NTsik0

*Code on `main`: [`src/contracts.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/src/contracts.py) (`FindDeadlines`, `Keyword`, `Limit`), [`src/tools.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/src/tools.py) (`find_deadlines`, registry entry), [`src/mcp_server.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/src/mcp_server.py) (`find_deadlines`), [`evals/tools/NTsik0.yaml`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/evals/tools/NTsik0.yaml), [`tests/test_find_deadlines.py`](https://github.com/NTsik0/TeamRepoAIPoweredApps/blob/main/tests/test_find_deadlines.py). Product pull request: [#18](https://github.com/NTsik0/TeamRepoAIPoweredApps/pull/18).*

**In one sentence, for the model:** List the deadlines in a course document, each quoted word for word with the section it comes from. Reads only.

| | |
|---|---|
| **Effect** | reads. No model call: every quote is copied from the document, so a date cannot be invented |
| **Undo** | nothing to undo: no state changes |
| **Idempotent?** | yes |
| **Offered to** | everyone, visitors included. It needs no identity, so offering it widely costs nothing |
| **Identity from** | not needed. An identity field sent in the arguments is still refused (`extra="forbid"`), not ignored |
| **Touches** | `data/courses/cs6920.md`, read only, through `load_course()`. No other file, no network |
| **Must never** | state a deadline that is not in the document, or build a file path from the model's text |

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
