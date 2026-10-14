# Retrieval spec · KIU CourseMate

*Lab 4 · one page. What CourseMate answers from, how it finds it, and when it refuses.*

## 1 · What the documents are

| Folder in `data/corpus/` | What is in it | Who owns the real version | How often it changes | Documents |
|---|---|---|---|---|
| `course/` | the CS6920 course overview: schedule, grading, AI policy | the course instructor | once a semester, plus corrections | 1 |
| `labs/` | the four lab pages (Labs 1 to 4) | the course instructor | once a week, as each lab is released | 4 |
| `homework/` | the homework page of each lab | the course instructor | weekly; deadlines can be extended | 4 |
| `milestones/` | the HW1 (Milestone 1) brief and the Design Review brief | the course instructor | when a deadline or rubric changes | 2 |
| `rules/` | the team repo guide: roles, workflow, tags, secrets | the course instructor | rarely | 1 |

Copied from the public course repository on 2026-10-14. The instructor's name and email were replaced with "the course instructor" and "email on Teams": the corpus holds no personal data.

Not in the corpus, on purpose: grades, Teams posts, exam content and rooms, anything about individual students. We refuse those and point to Teams or the instructor.

**Known risk:** the documents disagree with each other. `homework/lab-1` still says HW1 is due "Thursday of Week 4"; `milestones/hw1` moved it to Tuesday 20 October. Golden question g4 checks that the answer gives the newer date.

## 2 · Chunking

- Split on: `## ` headings. Each section of the course pages covers one topic.
- Header glued to each chunk before embedding: `title · section`, for example `Milestone 1 · HW1 "Spec to Ship" … · 4 · How to submit, step by step`
- Maximum size: 1,200 characters (about 300 tokens) · Overlap: one paragraph when a section is split

## 3 · Retrieval

- Embedding model: `openai/text-embedding-3-small` · $0.02 per million tokens (same price as the course reference; re-check on openrouter.ai before trusting a cost figure)
- Retriever: hybrid, vectors and BM25 merged with Reciprocal Rank Fusion · k = 8 (decision 0002; k = 5 missed the updated HW1 page for a typo question)
- Refusal threshold: best cosine score 0.25 (starting value; tuned with the golden set, see `docs/decisions/0002-k-equals-8.md`)

## 4 · Answering

- Model: `google/gemini-3.8-flash` from `COURSEMATE_MODEL` ($0.75 in / $3.75 out per million tokens)
- Reply shape: `{answer, citations, grounded}`, validated with pydantic, extra fields forbidden
- Every sentence cites a retrieved source as `[n]`. A citation that fails the check is a refusal, never a warning.
- Refuse before calling the model when nothing scores above the threshold.

## 5 · What the user sees

- A cited answer: "HW1 is due Tuesday 20 October 2026, 23:59 (Tbilisi time) [1]." with a source chip `[1] Milestone 1 · … · 4 · How to submit` that the student can open.
- A refusal: "I can't answer that from the CS6920 course documents." Next step offered: ask in the course channel on Teams.

## 6 · Acceptance criteria

- AC1 "What is the late penalty for HW1?" returns `answered`, citing `homework/lab-1`, and the answer says "10%"
- AC2 a question nothing in the corpus matches returns `refused` without a model call (`tests/test_answer.py`)
- AC3 a reply citing `[12]` when 8 sources were retrieved is refused (`tests/test_answer.py`)
- AC4 every answer and refusal writes one line to `logs/answers.jsonl` with the reason; every model call writes one line to `logs/usage.jsonl` with tokens, cost and latency
- AC5 `evals/golden.yaml` passes at 0.70 or above, run live

Endpoint: `POST /ask/grounded {"question": "..."}`. The Week 2 keyword endpoint `POST /ask` stays until the live golden run passes (decision 0003).
