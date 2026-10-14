# Lab 4 · Homework

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

---

## Milestone 1, in one screen

Unchanged since Lab 3. Same folder, same rubric (correctness 40 · code quality 20 · documentation and journal 20 · verification evidence 20).

```
hw1/<your-github-username>/
├── spec.md          one page: goal, users, acceptance criteria, context list, out of scope
├── golden.md        3 golden questions: question · expected · actual · pass or fail · how you ran it
├── delegation.md    half a page: what you delegated, what came back wrong, how you caught it
├── journal.md       Pattern Journal entries for Weeks 1, 2, 3 and 4
└── src/             the working feature, with at least one test that runs with `pytest hw1/<username>`
```

Branch `hw1-<your-github-username>` → pull request → a teammate approves (checks only that you stayed inside your folder) → merged to `main` → form on Teams with the link to your folder. Both the folder and the form are required.

Filled example: `Lab-3/examples/hw1-example/`. Everything else, including grading weights and the questions I expect: `Lab-3/MILESTONE-1.md`.

## Design Review, in one screen

```
docs/DESIGN-REVIEW.md      four pages at most, from Lab-4/templates/DESIGN-REVIEW.md
  1 Problem, users, success criteria ........ 2
  2 Architecture and data flow .............. 2
  3 Risks and safety threats ................ 2
  4 Evaluation plan, golden set run ......... 2
  5 Token budget, from your logs ............ 1
  6 Team, roles and decisions ............... 1
tag design-review on main  →  team form from the repo keeper
```

Every claim points at something already in your repo: `docs/spec.md`, your Lab 3 `docs/confidence-policy.md`, tonight's `evals/golden.yaml` and its result, your `logs/usage.jsonl`, `TEAM-CONTRACT.md`. We grade the commit the tag points to at 23:59 on Tuesday. Filled example: `Lab-4/examples/DESIGN-REVIEW-campuspulse.md`.

## Quiz 1, in one screen

Four kinds of question: **trace** (here is a log or an output: what happened, and why), **trade-off** (choose a design and defend it), **ladder** (place a delegation on the Autonomy Ladder and say how you verify it), **apply** (which pattern fits a new product, and what you build). Each answer is marked 1, ½ or 0. Write it yourself, in your own words. Short and specific beats long and polished.

## What this week's lab gives you toward them

- Your Week 4 journal entry (written in studio, finished after lab) is the fourth entry in `journal.md`: the pattern, one place you saw it or used it, one thing you would do differently.
- `golden.md` keeps the Lab 3 table format. Tonight's `evals/golden.yaml` shows how to write an expected answer precisely enough that a script could check it: copy that habit, not the file.
- The golden set result you commit in Part 3 is the evidence for section 4 of the Design Review, and your usage log is the evidence for section 5.

## Every deadline in the course

`SUBMISSIONS.md` at the root of this repo. On any conflict between files, that one wins. Stuck? Email the instructor (email on Teams) before the deadline, not after.
