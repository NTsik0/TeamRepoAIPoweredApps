# Pattern Journal · Guram Tsiklauri (Gaaa-3) · Weeks 5 to 7

> **FILL · read this first.** Weeks 5 and 6 below are drafted from what actually happened in this repo, so every fact in them is checkable. The *noticing* has to be yours: read each entry, cut what you did not think, and put the rest in your own words. Week 7 cannot be written yet — the lecture is on 5 November 2026. Delete this box before submitting.

*One entry per week: the pattern, one place I saw or used it, what I noticed, and one thing I would do differently.*

## Week 5 · Tool Contract
*Written 2026-10-31*

**Where I used it:** HW2, my tool `search_course_docs`. The function it wraps already existed and already worked: `hybrid()` from Week 4, which ranks the sections of `data/corpus/` for a question. So almost nothing in the slice was retrieval. It was the contract around it: a pattern on `question`, bounds of 1 to 5 on `k`, `extra="forbid"`, and a failure written as a sentence the model can act on ("ask a shorter question in the words the course uses") instead of an exception.

**What I noticed:** two things. First, the design work was deciding what *not* to return. `hybrid()` hands back `Hit` objects carrying a cosine score, and my first instinct was to pass all of it through. The model cannot do anything with 0.565; what it needs is the document name so it can cite it. The result shape is `source`, `heading`, `text`, and the score stays inside the tool, where it is used for the one decision it is good for: refusing. Second, the function had no way to refuse before I wrapped it. `hybrid()` always returns `k` sections, however irrelevant, so an off-topic question used to come back with the least bad match and no signal that it was bad. Putting it behind a contract is what forced me to pick a floor and write the refusal, and that is now the only part of the tool that is really mine.

**Do differently:** write the failure message first, before the happy path. I wrote mine last and it showed: the first version named `data/corpus/` in the text, which tells the model about our filesystem and tells the student nothing.

## Week 6 · Session State
*Written 2026-10-31*

**Where I saw it:** the Week 6 lecture, and then in my own code an hour later. The rule I wrote down was that every piece of state the product keeps gets one row — scope, lifetime, when it is written, how it is deleted — and if it has no row, the product does not keep it.

**What I noticed:** my tool stores nothing per student, so I thought the rule did not apply to me. It does. `corpus_index()` is wrapped in `lru_cache`, and a cache is state: its scope is the process, its lifetime is "until the process restarts", it is written on the first call, and there is no way to clear it. That has a consequence I had not thought about. Rebuilding `data/index/` or adding a document to `data/corpus/` changes nothing for a running server — it keeps answering from the index it built when the first question arrived. And I did not invent this: `get_index()` in `src/app.py` has been doing the same thing since Week 4, which is why I copied it without thinking. Two caches, one rule, and neither of us had written the row.

**Do differently:** write the row before the cache, not after. I only went looking because the lecture told me to look for rows rather than for bugs, and the fix cost one line in `docs/tool-contracts.md` ("built once per process; a rebuilt index or a changed corpus needs a restart"), which is exactly the thing a reviewer needs and the code does not say.

## Week 7 · Supervised Autonomy Loop
*To be written after the Week 7 lecture (5 November 2026).*

> **FILL** — after the lecture, write it the same way: the pattern, one place I saw or used it this week, what I noticed, one thing I would do differently. The obvious place to look is this homework itself: the red run was a supervised loop with the gate as the supervisor.
