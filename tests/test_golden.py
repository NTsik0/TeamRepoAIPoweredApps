"""The golden set itself: its scorer, its composition, and an offline run at k=5."""
import json
from collections import Counter
from pathlib import Path

import yaml

from evals.run_golden import score
from src.answer import Answer, answer

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = yaml.safe_load((ROOT / "evals" / "golden.yaml").read_text())
ITEM = {"expect": "answered", "must_cite": ["milestones/hw1"], "must_mention": ["20 October"]}


def answered(text, *doc_ids):
    return Answer("answered", text, [{"n": i, "doc_id": d} for i, d in enumerate(doc_ids, 1)])


def test_score_passes_a_correct_cited_answer():
    assert score(ITEM, answered("Due Tuesday 20 October [1].", "milestones/hw1")) == (True, [])


def test_score_fails_the_wrong_source():
    ok, why = score(ITEM, answered("Due Tuesday 20 October [1].", "homework/lab-1"))
    assert not ok and why == ["did not cite milestones/hw1"]


def test_score_fails_a_missing_fact():
    ok, why = score(ITEM, answered("Due Thursday of Week 4 [1].", "milestones/hw1"))
    assert not ok and "did not mention '20 October'" in why


def test_score_fails_an_answer_where_a_refusal_was_expected():
    ok, why = score({"expect": "refused"}, answered("The midterm is in room A112 [1].", "course/overview"))
    assert not ok and why[0].startswith("expected refused")


def test_golden_set_follows_the_week_4_composition():
    assert Counter(i["type"] for i in GOLDEN["items"]) == {"factual": 2, "reasoning": 1, "edge": 1, "refusal": 1}
    assert GOLDEN["threshold"] == 0.70


def test_every_must_cite_points_at_a_real_document():
    for item in GOLDEN["items"]:
        for doc in item["must_cite"]:
            assert (ROOT / "data" / "corpus" / f"{doc}.md").exists(), f"{item['id']} cites missing {doc}"


def test_offline_run_retrieves_the_right_documents_at_default_k(index):
    """Offline the 'model' only copies sentences, so this checks retrieval, not answer quality."""
    from src.answer import DEFAULT_K
    from src.search import hybrid
    for item in GOLDEN["items"]:
        if item["expect"] == "answered":
            got = {h.chunk.doc_id for h in hybrid(index, item["question"], k=DEFAULT_K)}
            missing = set(item["must_cite"]) - got
            assert not missing, f"{item['id']} did not retrieve {missing}"


def test_usage_summary_counts_only_live_calls(tmp_path, monkeypatch):
    from evals import usage_summary as us
    usage, answers = tmp_path / "u.jsonl", tmp_path / "a.jsonl"
    usage.write_text("\n".join(json.dumps(x) for x in [
        {"kind": "chat", "model": "google/gemini-3.8-flash", "prompt_tokens": 2000, "completion_tokens": 200,
         "cost_usd": 0.00225, "latency_ms": 1200},
        {"kind": "embed", "model": "openai/text-embedding-3-small", "prompt_tokens": 10, "completion_tokens": 0,
         "cost_usd": 0.0000002, "latency_ms": 100},
        {"kind": "chat", "model": "offline/trigram-hash", "prompt_tokens": 50, "completion_tokens": 5,
         "cost_usd": 0.0, "latency_ms": 0}]))
    answers.write_text("\n".join(json.dumps({"status": s}) for s in ["answered", "refused"]))
    monkeypatch.setattr(us, "USAGE", usage)
    monkeypatch.setattr(us, "ANSWERS", answers)
    s = us.summarise()
    assert s["chat_calls"] == 1 and s["embed_calls"] == 1          # the offline line is ignored
    assert s["avg_chat_cost_usd"] == 0.00225 and s["chat_latency_ms_p95"] == 1200
    assert s["answered"] == 1 and s["refused"] == 1
