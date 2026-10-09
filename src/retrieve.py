"""Keyword-overlap retrieval over course sections (Weeks 2 to 3; embeddings replace it in Week 4).

A section's score is the number of distinct question keywords that appear in its
title or text. Sections scoring below RELATIVE_THRESHOLD of the best score are
dropped, so one shared common word ("due") does not pull in unrelated sections.
"""
import re

from src.courses import Section

MAX_SECTIONS = 3
MAX_CHARS = 4000
RELATIVE_THRESHOLD = 0.6

STOPWORDS = {
    "a", "an", "and", "are", "about", "at", "be", "by", "can", "do", "does", "for", "from",
    "how", "i", "in", "is", "it", "me", "my", "of", "on", "or", "the", "this", "to", "we",
    "what", "when", "where", "which", "who", "why", "will", "with", "you", "your",
    "course", "tell", "much", "there", "any",
}


def keywords(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS}


def retrieve(sections: list[Section], question: str) -> list[Section]:
    q = keywords(question)
    if not q:
        return []
    scored = [(len(q & keywords(s.title + " " + s.text)), i, s) for i, s in enumerate(sections)]
    scored = [x for x in scored if x[0] > 0]
    if not scored:
        return []
    best = max(score for score, _, _ in scored)
    scored = [x for x in scored if x[0] >= best * RELATIVE_THRESHOLD]
    scored.sort(key=lambda x: (-x[0], x[1]))

    hits: list[Section] = []
    used = 0
    for _, _, s in scored[:MAX_SECTIONS]:
        room = MAX_CHARS - used
        if room <= 0:
            break
        text = s.text if len(s.text) <= room else s.text[:room]
        hits.append(Section(s.title, text))
        used += len(text)
    return hits
