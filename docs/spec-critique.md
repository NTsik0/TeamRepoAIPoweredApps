# Lab 1 drill · agent critique of spec v0

Agent: Claude (Opus 5.5), given `docs/spec.md` (v0) and `AGENTS.md` (v1). What came back, and what the team did with it.

## Prompt 1 · "List the three biggest ambiguities an engineer would hit building this."
1. **What counts as "grounded"?** v0 never says how the course document reaches the model: whole file, sections, or search results, nor how large. An engineer could send the entire document every time (cost) or invent retrieval. → Adopted: v1 Context list (3 sections, 4,000 chars, keyword overlap until Week 4).
2. **What happens when the answer isn't there?** AC2 says "instead of a guess" but not who decides it's missing (the model or the code), the exact wording, or whether the model is still called. → Adopted: v1 AC2 (code decides, fixed text, zero model calls).
3. **What does the API look like?** No endpoint, request or response shape, and no error behaviour (empty question, unknown course, model down). → Adopted: v1 API section and AC3 error shape.

Also suggested:
4. Add a `confidence` score (0 to 1) to every response so the UI can show uncertainty.
5. Support several courses in one question ("compare the grading of CS6920 and CS6100").
6. Store every question in a database for analytics.

## Prompt 2 · "Rewrite our success criteria so each one is measurable."
| v0 | Suggested |
|---|---|
| Correct answer quickly | ≥ 9 of 10 golden questions pass; p95 latency < 3 s from the usage log |
| Cheap enough for a whole course | average cost per answered question < $0.003 from logged tokens |
| Doesn't make up deadlines | 100% of "not in the documents" golden questions return the refusal text |

→ Adopted into v1 "Success criteria" as written.

## Rejected (fill in: the one you note in your Pattern Journal)
- [Which suggestion did the team reject, and why? Candidates above: 4, 5 or 6.]
