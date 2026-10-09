# 0001 · Keyword retrieval until Week 4

**Date:** Week 2 · **Decided by:** Nikoloz Tsikaridze; approved in review by Guram Tsiklauri (PR #2)

**Context.** The first slice must send only relevant course sections to the model (spec Context list, AC1) and refuse without a model call when nothing matches (AC2). Embeddings and RAG are taught in Week 4.

**Decision.** Score `## ` sections by distinct keyword overlap with the question (stopwords removed), keep those at 0.6 or more of the best score, at most 3 sections and 4,000 characters.

**Alternatives.** Send the whole course document every time: simplest, but around 2,500+ prompt tokens per question and the model sees everything, so "not in the documents" depends on the model alone. Embeddings now: better recall on paraphrases, but needs an embedding model, a store and API calls in tests before we have learned the pattern.

**Consequences.** Cheap, deterministic, testable without a key. Misses paraphrases ("homework deadline" vs "HW1 is due" works only through shared words) and synonyms. We will watch golden questions that fail on wording; Week 4 replaces `src/retrieve.py` behind the same function signature.
