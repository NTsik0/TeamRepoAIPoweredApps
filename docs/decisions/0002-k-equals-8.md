# 0002 · Retrieve k = 8 chunks, not 5

**Date:** Week 4 (2026-10-14) · **Decided by:** Nikoloz Tsikaridze; to be confirmed by the live run

**Context.** The HW1 deadline appears in six of our twelve documents, and two of them (`homework/lab-1`, `homework/lab-2`) still give the old date. For the typo question g4 ("wen is hw1 due") those old pages rank highest, and at k = 5 the updated page, `milestones/hw1`, is not retrieved at all. A model cannot cite the right date from a page it never sees.

**Decision.** Use k = 8 (`DEFAULT_K` in `src/answer.py`).

**Evidence.** Golden set run offline at both settings, committed in `evals/results/`:

| k | Right sources retrieved | Pass rate (offline) | Prompt size |
|---|---|---|---|
| 5 | 4 / 5 (g4 misses `milestones/hw1`) | 0.40 | about 1,700 tokens |
| 8 | 5 / 5 | 0.40 | about 2,600 tokens |

The offline pass rate is the same at both settings because the offline stand-in only copies sentences: it cannot refuse g5 on meaning or pick the newer of two dates. Only "right sources retrieved" is meaningful offline. The live run (real embeddings, real model) decides; its results go in `evals/results/` and this record is updated.

**Alternatives.** k = 5 (cheaper, but loses the one document that is right). Removing the outdated pages from the corpus (they are real course pages students read; the conflict is the real problem). Ranking newer documents higher (needs a "last updated" field per document; a candidate for Week 10).

**Consequences.** About 55% more prompt tokens per answer: roughly $0.0027 instead of $0.0020 per question at the promotional price. Watch the live golden run: if k = 5 passes g4 live, go back to 5.
