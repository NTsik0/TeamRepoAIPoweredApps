# Spec v0 · KIU CourseMate

## Problem
Course information at KIU is scattered across syllabi, GitHub READMEs, Teams announcements and emails. Students miss deadlines and ask the same questions repeatedly ("when is HW1 due?", "how much is the midterm worth?"), and instructors answer them one by one.

## Users
KIU students enrolled in a course who need a quick, correct answer about it. Secondary: instructors and TAs, who answer fewer repeated questions.

## Success criteria
1. A student gets a correct answer to a course question quickly.
2. Answers are cheap enough to run for a whole course.
3. The assistant does not make up deadlines or rules.

## Core feature (Weeks 2 to 4 scope)
Ask a question about one course in plain language, get an answer grounded in that course's documents, with the section it came from. No accounts, no uploads yet.

## Context list
- `data/courses/<course-id>.md` (the course's README/syllabus, split into sections) · in the repo
- The course id the student picked
- Nothing else. Personal data, grades and Teams posts are out.

## Acceptance criteria
1. "When is HW1 due?" for CS6920 returns the date and time from the course document.
2. A question the document does not answer gets "I can't find that in the course documents" instead of a guess.
3. Every response logs prompt tokens, completion tokens and latency.

## Napkin math
300 req/day × (2,500 × $0.75 + 200 × $3.75) / 1M × 30 ≈ $24/month on gemini-3.8-flash (prices per 1M tokens; re-check openrouter.ai/models).

## Risks and safety
- Outdated course document gives a confident wrong deadline. Mitigation: show the document's last-updated date in the answer.
- Hallucinated rules. Mitigation: answer only from retrieved sections, cite the section, refuse otherwise.
- Off-topic or misuse questions. Mitigation: system prompt scopes it to the course; refuses the rest.

## Out of scope (for now)
Accounts, grades, uploading new syllabi, Georgian language, Teams integration, multiple courses in one question.
