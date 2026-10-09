# Spec v1 · KIU CourseMate

## Goal
Answer KIU students' questions about one course (deadlines, grading, policies, schedule) correctly, quickly and cheaply, using only that course's official documents, and say so plainly when the documents don't contain the answer.

## Users
- **Primary:** KIU students enrolled in a course who need one fact fast ("When is HW1 due?").
- **Secondary:** instructors and TAs, who answer fewer repeated questions.

## Success criteria (measurable)
1. **Correctness:** at least 9 of 10 golden questions pass (Week 4 set; Week 11 threshold 0.70 as a floor).
2. **Grounding:** 100% of "not in the documents" golden questions return the refusal text, never an invented answer.
3. **Latency:** p95 end-to-end latency under 3 s, measured from `logs/usage.jsonl`.
4. **Cost:** average cost per answered question under $0.003, measured from logged token counts.

## Context list
- `data/courses/<course-id>.md`: the course document, split into sections at `## ` headings. In the repo; humans edit it.
- The `course_id` the student sends.
- At most 3 retrieved sections, at most 4,000 characters in total, go to the model. Nothing else: no personal data, grades, chat history or Teams posts.

## API
`POST /ask` with JSON `{"course_id": "cs6920", "question": "When is HW1 due?"}`

Success (200):
```json
{"course_id": "cs6920", "answer": "...", "found": true, "sources": ["Homework"]}
```
Error (4xx/5xx), always this shape:
```json
{"error": {"code": "question_empty", "message": "..."}}
```
`GET /health` returns `{"status": "ok"}`.

## Acceptance criteria (each decidable by a script)
- **AC1 · Grounded answer.** For a question whose keywords match a section of the course document, the response is 200 with `found: true`, `sources` lists the matched section headings (1 to 3), the model receives only those sections, and the model's text is returned as `answer`. Checked by: unit test with a fake model; golden question "When is HW1 due?" → answer contains "Thursday of Week 4" and "23:59".
- **AC2 · Refusal, no model call.** For a question that matches no section, the response is 200 with `found: false`, `sources: []`, `answer` exactly `"I can't find that in the course documents."`, and the model is called zero times. Checked by: unit test counting fake-model calls.
- **AC3 · Error shape.** Empty or whitespace-only question → 422 `question_empty`; question over 500 characters → 422 `question_too_long`; unknown `course_id` → 404 `course_not_found`; model call fails → 502 `model_error`. Every error body matches `{"error": {"code", "message"}}`. Checked by: unit tests, one per code.
- **AC4 · Usage log.** Every model call appends exactly one JSON line to `logs/usage.jsonl` with `ts`, `course_id`, `model`, `prompt_tokens`, `completion_tokens`, `latency_ms`. No question text, no key. Checked by: unit test reading the log file.
- **AC5 · Cost and latency cap.** Context sent to the model is at most 3 sections and 4,000 characters; `max_tokens` is 300. That is about 1,300 prompt tokens and 300 completion tokens, so at gemini-3.8-flash prices one answer costs at most about $0.0021. Checked by: unit test on the prompt builder; p95 latency from the usage log in Week 4.

## Constraints
- Python 3.11, FastAPI, OpenRouter. Model from env `COURSEMATE_MODEL`, default `google/gemini-3.8-flash`.
- Key only from env `OPENROUTER_API_KEY`. Tests never call a real model and need no key.
- Retrieval in Weeks 2 to 3 is keyword overlap over sections. Embeddings replace it in Week 4 (decision record 0001).

## Napkin math
300 req/day × (1,300 × $0.75 + 200 × $3.75) / 1M × 30 ≈ $16/month on gemini-3.8-flash (prices per 1M tokens; re-check openrouter.ai/models). Refusals (AC2) cost $0. v0 assumed 2,500 prompt tokens; the AC5 context cap brings it down.

## Risks and safety
- **Outdated course document → confident wrong deadline.** Mitigation: each document carries a "Last updated" line; shown in answers from Week 3.
- **Hallucinated rules.** Mitigation: model sees only retrieved sections; system prompt requires citing them and refusing otherwise; AC2 refuses before any model call.
- **Prompt injection inside a course document.** Mitigation: documents are human-edited only (AGENTS.md Never list); red-teamed in Week 12.
- **Off-topic misuse.** Mitigation: off-topic questions match no section → AC2 refusal.

## Out of scope (for now)
Accounts, grades, uploading new syllabi, Georgian language, Teams integration, streaming, multiple courses in one question, embeddings (Week 4).

## First slice (Lab 2)
Criteria: AC1, AC2, AC4
Done when: `pytest` passes on a clean clone with tests for AC1 (grounded answer via fake model), AC2 (refusal with zero model calls) and AC4 (one usage line per model call), and CI is green.
Not in this slice: AC3 error codes and shape (next slice), AC5 measurement, real retrieval quality, golden-set runner, UI, any other course than `cs6920`.

## Verification
- Command: `pytest` (collects `tests/` only, per `pytest.ini`).
- Green means: all tests pass with no network access and no `OPENROUTER_API_KEY` set, locally and in CI (`.github/workflows/ci.yml`, job `test`).
