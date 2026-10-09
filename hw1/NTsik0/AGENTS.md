# AGENTS.md · HW1 Deadline Finder (NTsik0)
Copied from the team AGENTS.md and narrowed to this folder. Spec: hw1/NTsik0/spec.md

## Commands
test:     pytest hw1/NTsik0
run:      python hw1/NTsik0/src/deadlines.py cs6920        (needs OPENROUTER_API_KEY)
golden:   python hw1/NTsik0/src/run_golden.py              (needs OPENROUTER_API_KEY; rewrites golden.md results)

## Conventions
- Work only inside hw1/NTsik0/. Do not import from the team src/.
- Model from env COURSEMATE_MODEL, default google/gemini-3.8-flash; key from env OPENROUTER_API_KEY only.
- Every model call appends one line to logs/hw1-usage.jsonl.
- The code, not the prompt, decides whether a deadline is grounded (AC2).
- Tests use a fake model; they never call OpenRouter.

## Always
- Run `pytest hw1/NTsik0` before saying you are done, and paste the result

## Ask first
- Adding a dependency

## Never
- Read or write .env, or print a key
- Delete, skip, or weaken a test to make it pass
- Write golden results by hand: they come from run_golden.py
