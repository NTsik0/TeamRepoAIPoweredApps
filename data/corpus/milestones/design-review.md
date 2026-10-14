# Design Review · what you hand in, how it is graded, and when

**Design Review · team · 10 points**
**Due: before Week 5 · Tuesday 20 October 2026, 23:59 (Tbilisi time)**
**Submit: `docs/DESIGN-REVIEW.md` merged to `main` in your team repo, the tag `design-review` on `main`, then one team form submitted by your repo keeper (link on Teams)**
**Deliver: four pages at most: problem and users, architecture and data flow, risks and safety threats, evaluation plan with your golden set run, token budget from your logs, team and decisions**
**Full brief, template and rubric: `Lab-4/DESIGN-REVIEW.md`**

This page is the single source of truth for the Design Review. If any other file says something different, this page wins.

---

## 1 · What it is

Your first capstone milestone. Four weeks in, your product has a spec, a team, a slice built through the Week 2 gates, a multimodal feature with a low-confidence path, and, after tonight, answers grounded in your own documents with a golden set. The Design Review puts that on four pages: what you are building, for whom, how it works, what could go wrong, how you will know it works, and what it costs.

It is not a pitch and not a plan for someday. **Every claim points at something in the repo:** a file, a log line, a test, a decision record. A short review that links to real things beats a long one that describes intentions.

## 2 · How to hand it in

1. Copy `Lab-4/templates/DESIGN-REVIEW.md` to `docs/DESIGN-REVIEW.md` in your team repo. Fill it as a team. A filled example for CampusPulse: `Lab-4/examples/DESIGN-REVIEW-campuspulse.md`.
2. Merge it to `main` through a pull request, like any other change. Your Lab 4 work (`lab4-rag`) should already be on `main`, because the evaluation section points at it.
3. Tag the commit you want graded, on `main`:
   ```
   git switch main && git pull
   git tag design-review && git push origin design-review
   ```
4. The repo keeper submits the team form (link pinned on Teams): repo link, tag name, every member's name.

**We grade the commit the tag points to at 23:59 on Tuesday 20 October.** Do not move the tag after the deadline. Need to fix something before then? `git tag -d design-review && git push origin :refs/tags/design-review`, then tag again.

All three parts count: the file on `main`, the tag, the form.

## 3 · The six sections and how each is graded

Four pages at most, not counting the architecture diagram. Short sentences, tables where they help, links to files instead of copying them.

| # | Section | Points | Full marks | Half marks | Zero |
|---|---|---|---|---|---|
| 1 | **Problem, users, success criteria** | 2 | a specific problem for named users; 2 to 4 success criteria a script or a log could check, linked to `docs/spec.md` | problem and users clear, but criteria vague ("easy to use", "fast") | missing, or describes a technology instead of a problem |
| 2 | **Architecture and data flow** | 2 | one diagram (Mermaid in the file, or an image in `docs/`) showing every model call, the retrieval path from Lab 4, the Lab 3 feature, your data stores and where a human is in the loop; one short paragraph per arrow that is not obvious | a diagram that omits the model calls or the data flow, or is not connected to the code | missing, or a generic "frontend, backend, AI" picture |
| 3 | **Risks and safety threats** | 2 | at least four risks specific to your product (wrong answers, privacy, misuse, cost, a vendor failing), each with a mitigation that exists or a dated plan, and an owner; the Lab 3 confidence policy and the Lab 4 refusal path appear here | risks listed without mitigations, or mitigations that are all "we will be careful" | missing |
| 4 | **Evaluation plan** | 2 | your Lab 4 golden set (`evals/golden.yaml`) with the committed result linked and the pass rate stated honestly; what you will add by Week 11 (ten questions, 3 factual, 2 reasoning, 2 edge, 2 refusal, 1 format) and what the threshold will block | a plan with no run, or a run with no plan | missing |
| 5 | **Token budget** | 1 | cost and latency per request **from your own usage logs** (not guesses), and a monthly estimate at a stated number of users and requests; the RAG-or-long-context choice with its arithmetic | estimates with no log behind them | missing |
| 6 | **Team, roles and decisions** | 1 | `TEAM-CONTRACT.md` on `main` with every member's name; roles from `docs/TEAM-REPO.md` section 1; at least two decision records in `docs/decisions/` linked (one can be the setting you tuned in Lab 4) | contract present, no decision records | no contract on `main` |

Total: 10 points. Half marks are given per section, so a section can score 0, ½ of its points, or all of them.

## 4 · Rules

- **Four pages at most.** About 1,600 words. A reviewer stops reading at page five.
- **Link, don't paste.** Point at `docs/spec.md`, `docs/confidence-policy.md`, `evals/results/...json`, `logs/` summaries. Paste a number, never a whole file.
- **Honest beats impressive.** A golden set at 3 out of 5 with a one-line diagnosis scores full marks in section 4. A 5 out of 5 with no committed result scores half.
- **No keys, no personal data,** in the file or anything it links to.
- **AI is allowed and logged.** If an agent drafted a section, say which one in `docs/delegation-log.md`. You are responsible for every sentence.

## 5 · The studio check-in (Lab 4)

In the last 20 minutes of Lab 4, I visit each team's breakout room for a short check-in. Bring the template open and your architecture sketched. I will ask two or three of these:

- Point at the arrow in your diagram where a wrong answer would hurt a user most. What stops it?
- Which golden question is the one you are least sure passes, and why?
- What did your logs say one request costs?
- Which decision would a new teammate question first? Where is it written down?

The check-in is feedback, not grading. Write down what I say: it is usually the difference between half and full marks in one section.

## 6 · Questions I expect

**Is it a presentation?** No. The file, the tag and the form. Nothing is presented.

**Does the Lab 4 tag need to be on `main` first?** Yes. Your evaluation section links to the golden result committed in Lab 4.

**Our capstone changed since Lab 1. Do we update `docs/spec.md` too?** Yes, in the same pull request or before it. The review and the spec must agree.

**Can one person write it?** The team is graded together and every member must be able to explain every section. Split the sections, then review each other's, through a pull request like any other change.

**What if our golden set fails?** Commit the result anyway and say why in one line. Section 4 rewards an honest run with a diagnosis.

**Where do I ask?** Teams, in the course channel, so everyone sees the answer. Office hours over Google Meet, booked by email: the instructor (email on Teams).
