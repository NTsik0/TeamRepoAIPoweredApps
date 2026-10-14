"""llm.py Week 4 additions: cost, text-only and image calls, embeddings, the grounded endpoint."""
import json
import os

import numpy as np
from fastapi.testclient import TestClient

from src import llm


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def live(monkeypatch):
    """Pretend we are online; record every request instead of sending it."""
    sent = {}

    def post(url, headers, json, timeout):
        sent[url] = json
        if url == llm.OPENROUTER_EMBED_URL:
            return FakeResponse({"model": llm.EMBED_MODEL, "usage": {"prompt_tokens": 12},
                                 "data": [{"embedding": [3.0, 4.0]} for _ in json["input"]]})
        return FakeResponse({"model": "google/gemini-3.8-flash",
                             "usage": {"prompt_tokens": 1000, "completion_tokens": 200},
                             "choices": [{"finish_reason": "stop", "message": {
                                 "content": '{"answer": "ok [1].", "citations": [1], "grounded": true}'}}]})

    monkeypatch.setattr(llm, "OFFLINE", False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(llm.httpx, "post", post)
    return sent


def test_cost_uses_the_listed_prices():
    assert llm.cost_usd("google/gemini-3.8-flash", 1_000_000, 0) == 0.75
    assert llm.cost_usd("google/gemini-3.8-flash", 0, 1_000_000) == 3.75
    assert llm.cost_usd("openai/text-embedding-3-small", 1_000_000, 0) == 0.02
    assert llm.cost_usd("unknown/model", 1_000_000, 0) == 0.0


def test_text_only_call_sends_no_image_and_logs_cost(monkeypatch):
    sent = live(monkeypatch)
    out = llm.complete_json("question", schema={"type": "object"})
    body = sent[llm.OPENROUTER_URL]
    assert [p["type"] for p in body["messages"][0]["content"]] == ["text"]
    assert body["temperature"] == 0 and body["response_format"]["type"] == "json_schema"
    assert out["grounded"] is True
    last = json.loads(open(os.environ["COURSEMATE_LOG_PATH"]).read().splitlines()[-1])
    assert last["kind"] == "chat" and last["cost_usd"] == llm.cost_usd("google/gemini-3.8-flash", 1000, 200)


def test_image_call_attaches_the_image(monkeypatch):
    sent = live(monkeypatch)
    llm.complete_json("read this announcement", image=b"\xff\xd8", schema={"type": "object"})
    content = sent[llm.OPENROUTER_URL]["messages"][0]["content"]
    assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_embed_returns_unit_vectors_and_logs_an_embed_line(monkeypatch):
    sent = live(monkeypatch)
    v = llm.embed(["a", "b"])
    assert sent[llm.OPENROUTER_EMBED_URL]["model"] == llm.EMBED_MODEL
    assert v.shape == (2, 2) and np.allclose(v[0], [0.6, 0.8])
    last = json.loads(open(os.environ["COURSEMATE_LOG_PATH"]).read().splitlines()[-1])
    assert last["kind"] == "embed"


def test_grounded_endpoint_refuses_off_topic_and_validates_input(index, monkeypatch):
    from src import app as app_module
    monkeypatch.setattr(app_module, "get_index", lambda: index)
    client = TestClient(app_module.app)
    r = client.post("/ask/grounded", json={"question": "zzqx vbnm plkj"})
    assert r.status_code == 200 and r.json()["status"] == "refused"
    assert client.post("/ask/grounded", json={"question": ""}).status_code == 422


def test_grounded_endpoint_without_an_index_returns_our_error_shape(monkeypatch):
    from src import app as app_module

    def missing():
        raise FileNotFoundError("data/index/meta.json")
    monkeypatch.setattr(app_module, "get_index", missing)
    r = TestClient(app_module.app).post("/ask/grounded", json={"question": "When is HW1 due?"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "index_missing"
