"""Grounding rules (Lab 4): every answer cites a retrieved source or refuses."""
import json
import os

import pytest

from src.answer import REFUSAL, Reply, answer, check_citations


def reply(text, cites, grounded=True):
    return Reply(answer=text, citations=cites, grounded=grounded)


def model_says(text, cites, grounded=True):
    def fake(prompt, schema=None):
        fake.prompt = prompt
        return {"answer": text, "citations": cites, "grounded": grounded}
    return fake


def no_model(prompt, schema=None):
    raise AssertionError("the model must not be called")


# check_citations: one test per way an answer can be unsupported

def test_valid_citations_pass():
    assert check_citations(reply("HW1 is worth 5 points [1]. It is individual [2].", [1, 2]), 5) is None


def test_answer_without_markers_is_rejected():
    assert check_citations(reply("HW1 is worth 5 points.", [1]), 5) == "answer has no citations"


def test_citation_to_a_source_never_retrieved_is_rejected():
    problem = check_citations(reply("HW1 is due on Friday [7].", [7]), 5)
    assert "never retrieved" in problem and "7" in problem


def test_markers_and_list_must_agree():
    assert "disagree" in check_citations(reply("Five points [1].", [1, 2]), 5)


def test_every_sentence_needs_a_citation():
    problem = check_citations(reply("HW1 is worth 5 points [1]. Good luck with it.", [1]), 5)
    assert problem.startswith("uncited sentence")


# answer(): the four routes of the contract

def test_refuses_without_calling_the_model_when_nothing_is_relevant(index):
    result = answer(index, "zzqx vbnm plkj", llm=no_model)
    assert result.status == "refused" and result.text == REFUSAL
    assert "below threshold" in result.reason


def test_refuses_when_the_model_says_the_sources_do_not_answer(index):
    result = answer(index, "Which room is the midterm exam in?",
                    llm=model_says("The sources do not name a room.", [], False))
    assert result.status == "refused" and result.reason.startswith("model:")


def test_refuses_an_invented_citation(index):
    result = answer(index, "When is HW1 due?", llm=model_says("HW1 is due on Friday [12].", [12]))
    assert result.status == "refused"
    assert "never retrieved" in result.reason


def test_without_the_check_the_invented_citation_reaches_the_user(index):
    result = answer(index, "When is HW1 due?", llm=model_says("HW1 is due on Friday [12].", [12]), check=False)
    assert result.status == "answered"          # this is exactly what check_citations protects against


def test_answered_sources_map_numbers_to_documents(index):
    fake = model_says("Late work loses 10% per 24 hours [1].", [1])
    result = answer(index, "What is the late penalty for HW1?", llm=fake)
    assert result.status == "answered"
    n1 = result.sources[0]
    assert n1["n"] == 1
    assert f"[1] {n1['title']} · {n1['section']}" in fake.prompt   # the number the model saw is the number we show


def test_every_answer_and_refusal_writes_one_log_line(index):
    log = os.environ["COURSEMATE_ANSWER_LOG"]
    before = sum(1 for _ in open(log)) if os.path.exists(log) else 0
    answer(index, "What is the late penalty for HW1?", llm=model_says("Minus 10% per 24 hours [1].", [1]))
    answer(index, "zzqx vbnm plkj", llm=no_model)
    lines = open(log).read().splitlines()
    assert len(lines) == before + 2
    last = json.loads(lines[-1])
    assert last["status"] == "refused" and "below threshold" in last["reason"]
    assert {"question", "status", "reason", "best_score", "retrieved", "cited"} <= set(last)


def test_reply_schema_forbids_extra_fields():
    with pytest.raises(Exception):
        Reply.model_validate({"answer": "x [1].", "citations": [1], "grounded": True, "confidence": 0.9})
    assert Reply.model_json_schema()["additionalProperties"] is False
