# AGENTS.md · KIU CourseMate

*Instructions for AI coding agents working in this repo. Keep it current; agents read this first.*

## What this project is
An AI assistant that answers KIU students' questions about their courses (deadlines, grading, policies, schedule), grounded only in the course documents stored in `data/courses/`. For students who don't want to dig through syllabi, Teams posts and READMEs to find one date.

## Stack
- Language: Python 3.11
- Framework: FastAPI
- Model access: OpenRouter · default model: google/gemini-3.8-flash
- Data: course documents as Markdown in `data/courses/<course-id>.md`, checked into the repo

## How to run
```
pip install -r requirements.txt
uvicorn src.app:app --reload
pytest
```

## Conventions
- Secrets come from environment variables (`OPENROUTER_API_KEY`). Never write a key into a file.
- Every model call reads and logs `usage` (prompt tokens, completion tokens, latency).
- Answers use only the course document; if the answer is not in it, say so.
- New features ship with at least one golden question in `/evals`.

## You may
- Create and edit files in `src/`, `tests/`, `docs/`, `evals/`
- Propose dependency changes (ask before adding)

## You may not
- Touch `.env`, CI config, or anything in `secrets/`
- Edit files in `data/courses/` (course data changes go through a human)
- Delete tests to make them pass
- Call paid APIs in loops without a cap
