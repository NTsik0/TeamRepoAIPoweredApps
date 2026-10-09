# KIU CourseMate

Answers KIU students' questions about a course (deadlines, grading, policies) from the official course documents, and says so when the answer isn't there. CS6920 capstone · Fall 2026 · KIU CourseMate team · Nikoloz Tsikaridze, Guram Tsiklauri

**Status:** Week 2 · `POST /ask` answers CS6920 questions from the course document, refuses when nothing matches, and logs token usage and latency for every model call.

## The problem
Course information at KIU is spread across syllabi, GitHub READMEs, Teams posts and emails. Students miss deadlines or ask the same question the instructor answered last week, and instructors answer it again.

## Demo
[2-minute narrated video, YouTube Unlisted: link] · [backup demo video, Week 14] · [deployed URL, from Week 12]

## Run it
```
export OPENROUTER_API_KEY=...          # your own key, never in a file
pip install -r requirements.txt && uvicorn src.app:app --reload
pytest
```
Then ask:
```
curl -s localhost:8000/ask -H 'content-type: application/json' \
  -d '{"course_id": "cs6920", "question": "When is HW1 due?"}'
```

## How it works
1. `src/courses.py` loads `data/courses/<course-id>.md` and splits it into sections at `## ` headings.
2. `src/retrieve.py` scores sections by keyword overlap with the question and keeps the top 3 (max 4,000 characters). No match → fixed refusal, no model call.
3. `src/llm.py` sends only those sections to OpenRouter (`google/gemini-3.8-flash` by default, `max_tokens` 300) and logs usage to `logs/usage.jsonl`.
4. `src/app.py` (FastAPI) returns `answer`, `found` and `sources`.

Key decisions: [docs/decisions/](docs/decisions/)

## Does it work? (evidence)
| What we measure | Result | Where |
|---|---|---|
| Unit tests | passing in CI | Actions tab, workflow `ci` |
| Golden set | [x / 5 in Week 4 · x / 10 at threshold 0.70 from Week 11] | `evals/` |
| Cost per request | [$, from Week 4] | `logs/usage.jsonl` |
| p95 latency | [s, from Week 4] | `logs/usage.jsonl` |

## Case study
[docs/case-study.md: what we built, what we delegated, what we measured, what we would change · from Week 13]

## Team and how we work
Nikoloz Tsikaridze (repo keeper), Guram Tsiklauri (spec keeper) · Team rules: [docs/TEAM-REPO.md](docs/TEAM-REPO.md) · Spec: [docs/spec.md](docs/spec.md) · Delegation log: [docs/delegation-log.md](docs/delegation-log.md) · Journals: [docs/journal/](docs/journal/) · Team contract: [TEAM-CONTRACT.md](TEAM-CONTRACT.md)
