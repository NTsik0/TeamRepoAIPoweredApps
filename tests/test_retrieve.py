"""Retrieval and course loading: the pieces behind AC1, AC2 and the AC5 context cap."""
from src.courses import Section, load_course
from src.retrieve import MAX_CHARS, MAX_SECTIONS, retrieve


def test_load_course_splits_on_h2_headings():
    sections = load_course("cs6920")
    titles = [s.title for s in sections]
    assert "Homework" in titles
    assert "Grading" in titles
    assert all(s.text.strip() for s in sections)


def test_load_course_unknown_or_unsafe_id_returns_none():
    assert load_course("nope-404") is None
    assert load_course("../AGENTS") is None


def test_retrieve_ranks_best_match_first():
    hits = retrieve(load_course("cs6920"), "When is HW1 due?")
    assert hits[0].title == "Homework"


def test_retrieve_no_overlap_returns_empty():
    assert retrieve(load_course("cs6920"), "What is the weather in Batumi tomorrow?") == []


def test_retrieve_stopwords_alone_do_not_match():
    assert retrieve(load_course("cs6920"), "what is the and of it?") == []


def test_retrieve_respects_section_and_char_caps():
    sections = [Section(title=f"S{i}", text=("hw1 deadline " * 200)) for i in range(6)]
    hits = retrieve(sections, "hw1 deadline")
    assert 1 <= len(hits) <= MAX_SECTIONS
    assert sum(len(h.text) for h in hits) <= MAX_CHARS
