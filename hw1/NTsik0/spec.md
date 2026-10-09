# HW1 Spec · Deadline Finder · NTsik0

*A thin slice of KIU CourseMate: list every deadline in a course document, without inventing any.*

## Problem
Deadlines in a course are scattered through the syllabus: HW1 under Homework, the team contract under Teams, the Repository Review under Demo Day. A student who wants "everything I must hand in" has to read the whole document and still misses some.

## Users
KIU students planning their week. Secondary: the CourseMate `/ask` endpoint, which can later reuse the list.

## Success criteria
1. All 3 golden questions in `golden.md` pass.
2. 0 invented deadlines: every `due` value returned appears word for word in the section it cites.
3. One call costs under $0.002 and finishes in under 5 s, measured from `logs/hw1-usage.jsonl`.

## Interface
`python hw1/NTsik0/src/deadlines.py cs6920` prints JSON:
```json
{"course_id": "cs6920",
 "deadlines": [{"item": "HW1 Spec to Ship", "due": "Thursday of Week 4 at 23:59 Tbilisi time", "section": "Homework"}],
 "dropped": 0}
```
Errors print `{"error": {"code": "...", "message": "..."}}` and exit with code 2.

## Context list
- `hw1/NTsik0/data/<course-id>.md`, split at `## ` headings.
- Only sections that mention a deadline word (`due`, `deadline`, `end of week`, `23:59`), at most 4,000 characters in total.
- Nothing else: no student data, no chat history.

## Acceptance criteria
- **AC1 · Grounded list.** For a known course, each returned deadline has `item`, `due` and `section`, `section` is one of the sections sent to the model, and `due` appears in that section's text (case and spacing ignored). Checked by: unit test with a fake model; golden G1 and G2.
- **AC2 · Invented dates are dropped.** A model item whose `due` is not in its cited section, or that cites a section that was not sent, is removed from `deadlines` and counted in `dropped`. Checked by: unit test where the fake model invents a date.
- **AC3 · Errors.** Unknown or unsafe course id → `course_not_found` with no model call. Model output that is not valid JSON in the asked shape → `model_bad_output`. Both use the error shape above and exit code 2. Checked by: unit tests; golden G3.
- **AC4 · Usage log.** Every model call appends one JSON line with `ts`, `course_id`, `model`, `prompt_tokens`, `completion_tokens`, `latency_ms`. Checked by: unit test reading the log.
- **AC5 · Cost cap.** At most 4,000 characters of context and `max_tokens` 400. Checked by: unit test on the context builder.

## Napkin math
One call ≈ 1,300 prompt tokens + 250 completion tokens on `google/gemini-3.8-flash`: (1,300 × $0.75 + 250 × $3.75) / 1M ≈ $0.0019. A student checking daily for a 15-week semester: about 100 calls ≈ $0.19. (Re-check prices at openrouter.ai/models.)

## Risks
- **Invented or reworded deadline.** Mitigation: AC2 verbatim check in code, not trust in the prompt.
- **Missed deadline** (in a section without a deadline word). Mitigation: golden questions cover the known ones; the keyword list is easy to extend.
- **Prompt injection inside the course document.** Mitigation: the document is human-edited; the prompt marks it as data.

## Out of scope
Sorting by calendar date (the document uses week numbers), reminders, multiple courses, the team `/ask` endpoint.
