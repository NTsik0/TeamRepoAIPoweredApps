"""Chunking, the index and hybrid retrieval over the course documents."""
import json

import numpy as np
import pytest

from src.bm25 import BM25
from src.chunk import MAX_CHARS, chunk_markdown
from src.index import IndexMismatch, load, save
from src.search import hybrid, rrf, search

DOC = """# Lab 9 · Deploy

## Before lab
Pull the repo.

## Homework
Due Tuesday, 23:59.
"""


def test_one_chunk_per_section_with_title_and_section():
    chunks = chunk_markdown("labs/lab-9", DOC)
    assert [c.section for c in chunks] == ["Before lab", "Homework"]
    assert [c.id for c in chunks] == ["labs/lab-9#1", "labs/lab-9#2"]
    assert chunks[1].embed_text().startswith("Lab 9 · Deploy · Homework\n")


def test_long_section_splits_with_one_paragraph_overlap():
    paras = [f"Paragraph {i}. " + "word " * 60 for i in range(8)]
    chunks = chunk_markdown("rules/long", "# Long\n\n## Rules\n" + "\n\n".join(paras))
    assert len(chunks) > 1
    assert all(len(c.text) <= MAX_CHARS + 400 for c in chunks)
    assert chunks[1].text.startswith(chunks[0].text.split("\n\n")[-1])    # the overlap


def test_empty_sections_are_dropped():
    assert [c.section for c in chunk_markdown("x/y", "# T\n\n## Empty\n\n## Full\nSomething.")] == ["Full"]


def test_real_corpus_loads(index):
    doc_ids = {c.doc_id for c in index.chunks}
    assert {"course/overview", "milestones/hw1", "milestones/design-review", "rules/team-repo-guide"} <= doc_ids
    assert len(doc_ids) == 12


def test_vectors_are_unit_length(index):
    assert np.allclose(np.linalg.norm(index.vectors, axis=1), 1.0, atol=1e-5)


def test_search_returns_k_hits_best_first(index):
    hits = search(index, "Design Review rubric sections and points", k=4)
    assert len(hits) == 4
    assert [h.score for h in hits] == sorted([h.score for h in hits], reverse=True)


def test_bm25_finds_exact_tags():
    docs = ["Tag lab3-multimodal at the end.", "Tag lab4-rag on main.", "Tag design-review before Tuesday."]
    assert int(np.argmax(BM25(docs).scores("where does lab4-rag go"))) == 1


def test_rrf_rewards_agreement_and_keeps_singletons():
    fused = rrf([[3, 1, 2], [1, 4]])
    assert fused[0] == 1
    assert set(fused) == {1, 2, 3, 4}


def test_hybrid_survives_a_typo(index):
    hits = hybrid(index, "desgin review rubric", k=5)
    assert hits[0].chunk.doc_id == "milestones/design-review"


def test_index_round_trip(index, tmp_path):
    save(index, tmp_path)
    again = load(tmp_path)
    assert len(again.chunks) == len(index.chunks) and np.allclose(again.vectors, index.vectors)


def test_index_built_with_another_model_is_refused(index, tmp_path):
    save(index, tmp_path)
    meta = json.loads((tmp_path / "meta.json").read_text())
    meta["embed_model"] = "openai/text-embedding-3-small"
    (tmp_path / "meta.json").write_text(json.dumps(meta))
    with pytest.raises(IndexMismatch):
        load(tmp_path)
