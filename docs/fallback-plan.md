# KIU CourseMate · Fallback Plan

*Lab 8, Step 1. Five lines, written before the router. The code that implements every line is `src/router.py`.*

1. **The call we protect first:** `complete_tools()` in `src/llm.py`, the model turn of the Lab 7 loop (`src/agent.py`, behind `POST /plan`). Today, if OpenRouter answers 503, the student gets a 502 and this body: `{"error":{"code":"model_unavailable","message":"the model call failed: HTTPStatusError"}}` (reproduced with a fake planner that raises the 503). If the model hangs instead, each of up to 6 steps waits the full `timeout=60` before failing.
2. **The chain:** `google/gemini-3.8-flash`, then `anthropic/claude-haiku-5.5`. Flash first because our golden set and every live check so far were run against it; Haiku second because it is another company, so one outage does not take both. Used by the `/plan` loop (job `chat`).
3. **The limit: 15 seconds.** Our live golden run on 2026-10-14 measured p50 4.7 s and p95 14.1 s (`docs/delegation-log.md`, entry 2; `docs/DESIGN-REVIEW.md` S4). 15 s is just above our own p95, so a normal slow answer still gets through and a call past it is not coming. Worst case with two models: 30 seconds, then the sentence.
4. **The lifetime: 600 seconds.** What can make a stored answer wrong is the course document: a human can correct a deadline in `data/courses/cs6920.md`, and a stored answer must not quote the old one for long. The date is not a risk, because `facts()` puts today's date in the system prompt and so in the cache key. Turns that offer tools are never cached, so every `/plan` step asks a model; the cache only serves plain questions with the same messages.
5. **The sentence:** "CourseMate cannot reach its models right now. No reminder was saved. Please try again in a minute."

## What we decided not to do

- **No retry of the same model.** The chain is the retry. `complete_tools()` uses `httpx`, which does not retry on its own.
- **No fallback for our own bugs.** A 400, 401 or 403, or a missing `OPENROUTER_API_KEY`, is raised, and `/plan` still answers with its 502. `tests/test_router.py::test_our_own_bug_is_raised_not_hidden_by_the_next_model` holds us to it.
- **The starter's check had to learn `httpx`.** The template's `temporary()` reads `error.status_code` and looks for `Connection` in the class name. Our calls raise `httpx.HTTPStatusError` (the status is on `error.response`) and `httpx.ConnectError`, so an untouched starter would have raised a real 503 instead of trying Haiku. Two tests cover this.

## Open questions

- Is Haiku good enough for our loop? Our golden set has never run against it. Until it does, the honest statement is: a second answer beats an error page.
- `/ask`, the streaming chat and embeddings still call the model directly. They move to the router one at a time.
- If Flash answers the first steps of a `/plan` run and then goes down, Haiku receives a conversation that carries Gemini's `reasoning_details`. We have not seen whether OpenRouter accepts that. If it does not, the 400 is raised (our rule), and the student gets the old 502, not the sentence.
