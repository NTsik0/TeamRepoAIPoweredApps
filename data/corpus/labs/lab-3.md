# Lab 3 · Multimodal I/O · `lab3-multimodal`

**Week 3 · live online · 2 hours · pattern: Uncertainty-Aware UX**
You leave with one feature in your capstone that turns an image into structured data, and an honest path for when it is not sure.

| What you hand in today | Where | When | Graded? |
|---|---|---|---|
| The tag `lab3-multimodal` on `main` (feature merged, tests green) | your team repo | end of lab | not on its own: it is evidence for the Design Review (Week 4) and the Repository Review |
| Nothing is uploaded to this course repo. Nothing new is graded this week. | | | |
| **Milestone 1 = HW1** keeps going, now due **Tuesday 20 October, 23:59** | `hw1/<your-github-username>/` + form | before Week 5 | 5 points · brief: [MILESTONE-1.md](MILESTONE-1.md) |

**Before lab (20 minutes):** watch the Week 3 recording and submit watch-check 1 (link on Teams). Pull your team repo at `lab2-agentic`. Export the team OpenRouter key in your shell (`resources/setup-and-troubleshooting.md` has the command for bash, zsh and PowerShell). Take four photos with your phone of the thing your product will read: clean, degraded, ambiguous, and one that is not what your feature expects at all.

**Lab clock:** 0:00 recap and watch-check answers · 0:15 my live demo (I break the reference pipeline with the torn poster, then fix it test-first) · 0:30 Parts 1 to 3 · 1:25 studio · 1:45 homework walk-through · 1:55 next week.

---

## Part 1 · Spec it first · 10 min

No code before a spec. Week 2's rule, still in force.

1. **Pick your input.** What image or document does a real user of *your* product have in their hand? A receipt, a menu, a timetable screenshot, a handwritten form, a PDF page. No obvious one? Say so at Checkpoint 1 and I will help you pick; do not invent a use case to satisfy the lab.
2. **Copy `templates/multimodal-spec.md` to `docs/multimodal-spec.md`** in your repo and fill it: the fields you extract, which are required, how each is normalised, and your four test images.
3. **Put the four photos in `tests/images/`** as `clean.jpg`, `degraded.jpg`, `ambiguous.jpg`, `not-applicable.jpg`, each under 2 MB. No faces, no real names, no ID documents.

The same template filled in for CampusPulse posters: `examples/multimodal-spec-campuspulse.md`. Read it first; it takes two minutes.

**Done when:** `docs/multimodal-spec.md` and the four images are committed on a branch.

## Part 2 · Image in, JSON out · 25 min

Same workflow as your Lab 2 slice (`docs/TEAM-REPO.md` section 4): open an issue, branch `slice-<issue>-<two-words>`, pull request, a teammate approves and squash-merges.

Delegate the build to your agent at **rung 3 of the Autonomy Ladder: the agent writes the code, you read every line of the diff before it is merged.** Point the agent at exactly three things: your `docs/multimodal-spec.md`, your `AGENTS.md`, and `examples/poster-extraction/` in this lab folder as the reference. Ask for a plan first. Quote these two spec lines in the task prompt, because agents skip them most: *evidence is nullable, never a guess* and *images are downscaled before sending*.

What must be in the diff. Check each one yourself:

| Must have | Why | If stuck |
|---|---|---|
| A JSON schema sent with the request, and the reply validated with pydantic in your code | the schema is the ask, validation is the check; both are needed | `resources/structured-extraction.md`, section "The ask and the check" |
| Every field returns `value`, `evidence`, `confidence`; `null` when unreadable, never a guess | evidence is what catches an invented answer | `examples/poster-extraction/src/extract.py` |
| The call goes through your `llm.py` and logs tokens, cost, latency | an image is tokens too; look at `tokens_in` | `examples/poster-extraction/src/llm.py` |
| The image is downscaled before sending (longest side 1024 px) | a 12-megapixel photo costs about ten times what it needs to | `resources/how-models-see-images.md` |
| One entry in `docs/delegation-log.md`: what you delegated, what came back wrong, how you caught it | same format as Lab 2 | `Lab-2/templates/delegation-log.md` |

**✅ Checkpoint 1 (around 0:55):** run your clean image. Show me validated JSON with evidence for each field, and the usage line in your log. Two or three of you will screen-share.

## Part 3 · The low-confidence path · 30 min

This is the part that matters. Anyone can get JSON from a clean photo.

1. **Copy `templates/confidence-policy.md` to `docs/confidence-policy.md`.** For each required field, write which signal sends it to which route: accept, confirm with the user, send to review, reject. Do not use the model's self-rated confidence alone; `resources/confidence-signals.md` shows five signals that beat it, with the torn-poster example.
2. **Implement the checks as a pure function**, `decide(extraction, today, ...)`: extraction in, decision out, no model call inside. The reference is `examples/poster-extraction/src/checks.py`, twenty lines.
3. **Every doubtful result gets a route and a reason a human can read.** Fields flagged missing or without evidence are *hard*: the reviewer sees them empty, never prefilled with the guess. How each route looks to the user is in `resources/designing-for-doubt.md`.
4. **Write at least three unit tests** for `decide()` with hand-written extractions, no API calls, in `tests/`. One must be your degraded image's case.
5. **Run your degraded image for real** and show that it lands on confirm or review.

**✅ Checkpoint 2 (around 1:25):** the degraded image is routed to confirm or review with readable reasons, `pytest` is green, the pull request is merged. Then tag, on `main`:

```
git switch main && git pull
git tag lab3-multimodal && git push origin lab3-multimodal
```

## Part 4 · Studio · 20 min

- **Team contract.** `TEAM-CONTRACT.md` at your repo root, from `Lab-1/templates/team-contract.md`, every member's name typed in. Teams of two to four lock this week; the contract is due at the end of Week 3 and is part of the Design Review.
- **AGENTS.md.** Add your multimodal conventions. At minimum: *never prefill a low-confidence value into a form*.
- **Journal.** Start your Week 3 entry in `docs/journal/<your-github-username>.md`: the pattern, one place you used it today, one thing you would do differently. Finish it after lab; it goes into Milestone 1.

Last 10 minutes: [HOMEWORK.md](HOMEWORK.md) on screen, line by line.

**Stretch:** run the extraction twice and flag the fields that disagree (`disagreements()` in `examples/poster-extraction/src/extract.py`).

---

## What your repo has at the end of Lab 3

| Path | Created in | Required |
|---|---|---|
| `docs/multimodal-spec.md` | Part 1 | yes |
| `tests/images/{clean,degraded,ambiguous,not-applicable}.jpg` | Part 1 | yes |
| `src/` extraction code with schema, validation, downscale, logged call | Part 2 | yes |
| `docs/delegation-log.md`, one new entry | Part 2 | yes |
| `docs/confidence-policy.md` | Part 3 | yes |
| `src/` a pure `decide()` function; `tests/` three or more tests for it | Part 3 | yes |
| tag `lab3-multimodal` on `main` | Checkpoint 2 | yes |
| `TEAM-CONTRACT.md` | Studio | by end of Week 3 |
| `AGENTS.md` multimodal lines; `docs/journal/<username>.md` Week 3 entry | Studio | yes |

## Folder map of this lab

- [MILESTONE-1.md](MILESTONE-1.md) · everything about HW1: deliverables, folder layout, submission steps, grading.
- [HOMEWORK.md](HOMEWORK.md) · what is due, in full.
- `templates/` · `multimodal-spec.md`, `confidence-policy.md`. Copy into your repo's `docs/`.
- `examples/` · both templates filled in for CampusPulse; `poster-extraction/`, a working reference with 33 offline tests, four synthetic posters and a review page; `hw1-example/`, a filled Milestone 1 folder.
- `resources/` · optional, and where the depth is: `how-models-see-images.md`, `structured-extraction.md`, `confidence-signals.md`, `designing-for-doubt.md`, `setup-and-troubleshooting.md`.

---

## Homework

**No new homework this week.** Nothing new is graded. Two things are already due, and both are listed here in full.

**Milestone 1 = HW1 · "Spec to Ship" · 5 points · individual**
**Due: before Week 5 · Tuesday 20 October 2026, 23:59 (Tbilisi time). Extended by one week from the original Week 4 date.**
**Submit: push to `hw1/<your-github-username>/` in your team repo (four files and one `src/` folder), then fill the submission form (link on Teams)**
**Deliver: a one-page spec, the working feature it describes, 3 golden questions with results, a half-page delegation log, and your Pattern Journal for Weeks 1 to 4**
**Full brief, folder layout and checklist: `Lab-3/MILESTONE-1.md`**

**Team contract · team · due end of Week 3 · part of your Design Review (10 points, Week 4)**
**Submit: `TEAM-CONTRACT.md` at your team repo root, from `Lab-1/templates/team-contract.md`, every member's name typed in**

```
hw1/<your-github-username>/
├── spec.md          one page: goal, users, acceptance criteria, context list, out of scope
├── golden.md        3 golden questions: question · expected · actual · pass or fail · how you ran it
├── delegation.md    half a page: what you delegated, what came back wrong, how you caught it
├── journal.md       Pattern Journal entries for Weeks 1, 2, 3 and 4
└── src/             the working feature, with at least one test that runs with `pytest hw1/<username>`
```

Full notes: [HOMEWORK.md](HOMEWORK.md) · every deadline in the course: `SUBMISSIONS.md` at the repo root.
