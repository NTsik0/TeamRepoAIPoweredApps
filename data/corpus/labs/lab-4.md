# Lab 4 · Grounded Generation · `lab4-rag`

**Week 4 · live online · 2 hours · pattern: Grounded Generation**
You leave with a feature in your capstone that answers from your own documents, cites them, refuses when it cannot, and a golden set that proves it.

| What you hand in today | Where | When | Graded? |
|---|---|---|---|
| The tag `lab4-rag` on `main` (feature merged, golden results committed) | your team repo | end of lab | not on its own: it is evidence for the Design Review and the Repository Review |
| **Milestone 1 = HW1** and the **Design Review** | your team repo + forms | **Tuesday 20 October, 23:59** | 5 points (individual) and 10 points (team) · see [HOMEWORK.md](HOMEWORK.md) |
| **Quiz 1** | Google Form | released after the Week 5 lecture | 5 points · format in [HOMEWORK.md](HOMEWORK.md) |

**Before lab (10 minutes, right after the lecture):** pull your team repo at `lab3-multimodal`. Export the team OpenRouter key (`resources/setup-and-troubleshooting.md` has bash, zsh and PowerShell). Collect **10 to 30 real documents your users would ask about**: help pages, rules, FAQs, product descriptions, past records. Markdown or plain text; paste PDFs into text. Shareable only: no personal data, no real names.

**Lab clock:** 0:00 recap and questions · 0:15 my live demo (I switch the citation check off, then a "save tokens" change gets caught by the golden set) · 0:30 Parts 1 to 3 · 1:25 studio: Design Review check-ins · 1:45 homework walk-through · 1:55 next week.

---

## Part 1 · Spec the corpus · 10 min

No code before a spec. Same rule since Week 2.

1. **Copy `templates/retrieval-spec.md` to `docs/retrieval-spec.md`** and fill it: which documents, who owns them and how often they change, your chunking rule, k, a starting threshold, what a citation looks like to your user, and the sentence a user sees when you refuse.
2. **Put the documents in `data/corpus/`**, one file per document, grouped in folders if it helps (`data/corpus/rules/`, `data/corpus/faq/`).
3. **Name five questions** your users would really ask, including one your documents cannot answer. You will need them in Part 3.

The CampusPulse version, filled in: `examples/retrieval-spec-campuspulse.md`. Two minutes to read.

**Done when:** `docs/retrieval-spec.md` and `data/corpus/` are committed on a branch.

## Part 2 · Retrieve, cite, or refuse · 25 min

Same workflow as every slice (`docs/TEAM-REPO.md` section 4): issue, branch `slice-<issue>-<two-words>`, pull request, a teammate approves and squash-merges.

Delegate at **rung 3: the agent writes the code, you read every line of the diff before it is merged.** Point the agent at exactly three things: `docs/retrieval-spec.md`, your `AGENTS.md`, and `examples/campuspulse-rag/` in this lab folder. Ask for a plan first. Quote these two lines in the task prompt, because agents skip them most: *refuse before calling the model when nothing scores above the threshold* and *every citation is checked in code; a failed check is a refusal, never a warning*.

What must be in the diff. Check each one yourself:

| Must have | Why | If stuck |
|---|---|---|
| `embed()` added to your Lab 3 `llm.py` through the same `client`, logging usage like every other call; `complete_json()`'s `image` made optional. Nothing else in the file changes, and your Lab 3 tests stay green | one logged path for every model call | `examples/campuspulse-rag/src/llm.py` · `resources/embeddings-explained.md` |
| An index that records which embedding model built it and refuses to load with a different one | vectors from two models are not comparable | `examples/.../src/index.py` |
| Retrieval that returns chunks **with scores** (vector, or hybrid with BM25) | the score is what makes refusal possible | `examples/.../src/retrieve.py` · `resources/chunking-and-retrieval.md` |
| A reply schema `{answer, citations, grounded}`, validated in your code; no confidence field | the model may say "not in my sources" | `examples/.../src/answer.py` · `resources/grounding-and-citations.md` |
| A citation check: unknown `[n]`, missing `[n]`, uncited sentence all refuse | a citation must point at something you retrieved | `check_citations()` in the same file |
| One log line per answer **and** per refusal, with the reason | the log entry half of the Evidence Rule | `_log()` in the same file |
| At least 3 offline unit tests in `tests/`: an invented citation is refused, a low score refuses **without calling the model**, an answer maps `[n]` to the right document | the test half of the Evidence Rule | `examples/.../tests/test_answer.py` |
| One entry in `docs/delegation-log.md` | same format as Lab 2 | `Lab-2/templates/delegation-log.md` |

**✅ Checkpoint 1 (around 1:00):** ask one question your documents answer and one they don't. Show me the cited answer, the refusal, and both log lines. Two or three of you will screen-share.

## Part 3 · Your first golden set · 20 min

1. **Copy `templates/golden-set.yaml` to `evals/golden.yaml`.** Five questions from *your* corpus: 2 factual, 1 reasoning (needs two documents), 1 edge case (a typo, a vague phrasing), 1 refusal. For each: `expect`, `must_cite`, `must_mention`, and a one-line `why`. Keep `must_mention` short and exact.
2. **Copy `examples/campuspulse-rag/evals/run_golden.py`** into `evals/` and fix the imports for your package. It runs the same function your app runs.
3. **Run it live, with the real model.** Commit the file it writes in `evals/results/`, pass or fail. A failing result with one honest line on why is worth more than a pass nobody can reproduce.
4. **Tune one setting** (k or the threshold), run again, keep the better one, and record the change as a decision in `docs/decisions/`.
5. **Turn on the Evidence Rule in your pull request template:** replace the "From Week 4 (Evidence Rule)" line in `.github/pull_request_template.md` with the two lines in `templates/pr-checklist-evidence.md`.

**✅ Checkpoint 2 (around 1:25):** golden results committed, pull request merged, `pytest` green. Then tag, on `main`:

```
git switch main && git pull
git tag lab4-rag && git push origin lab4-rag
```

## Part 4 · Studio · 20 min

- **Design Review.** Copy `templates/DESIGN-REVIEW.md` to `docs/DESIGN-REVIEW.md` and draft it together. I visit each team for a short check-in: have the template open and your architecture sketched. Brief and rubric: [DESIGN-REVIEW.md](DESIGN-REVIEW.md).
- **AGENTS.md.** Add your grounding rules. At minimum: *every answer cites a retrieved source or refuses* and *never weaken or delete a golden question to make it pass*.
- **Journal.** Write your Week 4 entry in `docs/journal/<your-github-username>.md`: the pattern, one place you used it today, one thing you would do differently. Finish it after lab; it is the fourth entry in Milestone 1.

Last 10 minutes: [HOMEWORK.md](HOMEWORK.md) on screen, line by line.

**Stretch:** run your golden set at `--k 1` and `--k 8`, and at two thresholds. Put the four pass rates in a small table in your decision record.

---

## What your repo has at the end of Lab 4

| Path | Created in | Required |
|---|---|---|
| `docs/retrieval-spec.md` · `data/corpus/` | Part 1 | yes |
| `src/` embed, index, retrieve, answer with citation check and refusal; one log line per answer | Part 2 | yes |
| `tests/` three or more offline tests for the grounding rules | Part 2 | yes |
| `docs/delegation-log.md`, one new entry | Part 2 | yes |
| `evals/golden.yaml` · `evals/run_golden.py` · `evals/results/<run>.json` | Part 3 | yes |
| `docs/decisions/` one record for the setting you tuned | Part 3 | yes |
| tag `lab4-rag` on `main` | Checkpoint 2 | yes |
| `docs/DESIGN-REVIEW.md` draft · `AGENTS.md` grounding lines · Week 4 journal entry | Studio | draft today, final by Tuesday 23:59 |

## Folder map of this lab

- [HOMEWORK.md](HOMEWORK.md) · what is due, in full. [DESIGN-REVIEW.md](DESIGN-REVIEW.md) · the Design Review brief and rubric.
- `templates/` · `retrieval-spec.md`, `golden-set.yaml`, `DESIGN-REVIEW.md`, `pr-checklist-evidence.md`.
- `examples/` · `retrieval-spec-campuspulse.md`, `DESIGN-REVIEW-campuspulse.md`, and `campuspulse-rag/`: a working reference with 37 offline tests, a 12-document corpus, a golden set, two committed results and the demo I run in lab.
- `resources/` · optional, and where the depth is: `embeddings-explained.md`, `chunking-and-retrieval.md`, `grounding-and-citations.md`, `golden-sets-and-the-evidence-rule.md`, `rag-or-long-context.md`, `setup-and-troubleshooting.md`.

---

## Homework

**No new individual homework this week.** Two things are due before Week 5 and Quiz 1 comes next week. All three are listed here in full.

**Milestone 1 = HW1 · "Spec to Ship" · 5 points · individual**
**Due: before Week 5 · Tuesday 20 October 2026, 23:59 (Tbilisi time). Extended by one week from the original Week 4 date.**
**Submit: push to `hw1/<your-github-username>/` in your team repo (four files and one `src/` folder), then fill the submission form (link on Teams)**
**Deliver: a one-page spec, the working feature it describes, 3 golden questions with results, a half-page delegation log, and your Pattern Journal for Weeks 1 to 4**
**Full brief, folder layout and checklist: `Lab-3/MILESTONE-1.md`**

**Design Review · team · 10 points**
**Due: before Week 5 · Tuesday 20 October 2026, 23:59 (Tbilisi time)**
**Submit: `docs/DESIGN-REVIEW.md` merged to `main` in your team repo, the tag `design-review` on `main`, then one team form submitted by your repo keeper (link on Teams)**
**Deliver: four pages at most: problem and users, architecture and data flow, risks and safety threats, evaluation plan with your golden set run, token budget from your logs, team and decisions**
**Full brief, template and rubric: `Lab-4/DESIGN-REVIEW.md`**

**Quiz 1 · individual · 5 points · covers Weeks 1 to 5**
**Released on Teams after the Week 5 lecture · Due: Tuesday 27 October 2026, 23:59 (Tbilisi time), before the Week 6 lab**
**Five written questions on a Google Form. You may use your slides. You may not use ChatGPT, Claude, Gemini, or any other AI tool to write or rewrite your answers. Every answer is run through Turnitin: if your answers do not meet the threshold for original work, your quiz mark is zero.**

```
hw1/<your-github-username>/
├── spec.md          one page: goal, users, acceptance criteria, context list, out of scope
├── golden.md        3 golden questions: question · expected · actual · pass or fail · how you ran it
├── delegation.md    half a page: what you delegated, what came back wrong, how you caught it
├── journal.md       Pattern Journal entries for Weeks 1, 2, 3 and 4
└── src/             the working feature, with at least one test that runs with `pytest hw1/<username>`
```

Full notes: [HOMEWORK.md](HOMEWORK.md) · every deadline in the course: `SUBMISSIONS.md` at the repo root.
