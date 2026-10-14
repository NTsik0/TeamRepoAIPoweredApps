"""Extraction shape, downscaling, and the /deadline/photo endpoint. No model is called."""
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

from src import deadline_extract as dx
from src.deadline_extract import DeadlineExtraction, Field, disagreements
from src.images import approx_image_tokens, downscale

IMAGES = Path(__file__).resolve().parent / "images"


def png(w, h):
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), (200, 30, 30, 255)).save(buf, format="PNG")
    return buf.getvalue()


def payload(**over):
    base = {"item": {"value": "HW1", "evidence": "HW1", "confidence": 0.9},
            "due_date": {"value": "2026-10-20", "evidence": "Tuesday 20 October 2026", "confidence": 0.9},
            "due_time": {"value": "23:59", "evidence": "23:59", "confidence": 0.9},
            "course": {"value": None, "evidence": None, "confidence": 0.0}}
    base.update(over)
    return base


def test_downscale_caps_longest_side_keeps_ratio_and_never_upscales():
    assert Image.open(io.BytesIO(downscale(png(3000, 4000)))).size == (768, 1024)
    assert Image.open(io.BytesIO(downscale(png(400, 300)))).size == (400, 300)


def test_downscale_returns_rgb_jpeg_without_exif():
    out = Image.open(io.BytesIO(downscale(png(800, 1100))))
    assert out.format == "JPEG" and out.mode == "RGB" and len(out.getexif()) == 0


def test_approx_tokens_grows_with_tiles():
    assert approx_image_tokens(700, 700) == 258 and approx_image_tokens(768, 1024) == 516


def test_schema_rejects_bad_confidence_and_missing_fields():
    with pytest.raises(ValidationError):
        Field(value="x", evidence="x", confidence=1.4)
    p = payload()
    del p["course"]
    with pytest.raises(ValidationError):
        DeadlineExtraction.model_validate(p)


def test_extract_downscales_before_sending(monkeypatch):
    seen = {}

    def fake(prompt, image=None, schema=None, **kw):
        seen.update(prompt=prompt, image=image, schema=schema)
        return payload()
    monkeypatch.setattr(dx, "complete_json", fake)
    x = dx.extract((IMAGES / "degraded.jpg").read_bytes())
    assert x.due_date.value == "2026-10-20"
    assert seen["image"][:2] == b"\xff\xd8"                                   # JPEG
    assert max(Image.open(io.BytesIO(seen["image"])).size) <= 1024            # downscaled
    assert "Never guess" in seen["prompt"] and seen["schema"]["title"] == "DeadlineExtraction"


def test_extract_raises_on_wrong_shape(monkeypatch):
    monkeypatch.setattr(dx, "complete_json", lambda *a, **k: {"item": "just a string"})
    with pytest.raises(ValidationError):
        dx.extract(png(100, 100))


def test_the_four_test_images_exist_and_are_small():
    for name in ("clean", "degraded", "ambiguous", "not-applicable"):
        path = IMAGES / f"{name}.jpg"
        assert path.exists() and path.stat().st_size < 2 * 1024 * 1024
        assert len(Image.open(path).getexif()) == 0                           # no location data


def test_disagreements():
    a = DeadlineExtraction.model_validate(payload())
    b = DeadlineExtraction.model_validate(payload(due_time={"value": "23:00", "evidence": "23:00", "confidence": 0.5}))
    assert disagreements(a, a) == [] and disagreements(a, b) == ["due_time"]


def test_endpoint_routes_and_blanks_hard_fields(monkeypatch):
    from src import app as app_module
    guessed = payload(due_date={"value": "2026-10-20", "evidence": None, "confidence": 0.95})
    monkeypatch.setattr(dx, "complete_json", lambda *a, **k: guessed)
    r = TestClient(app_module.app).post("/deadline/photo",
                                        files={"image": ("d.jpg", (IMAGES / "degraded.jpg").read_bytes(), "image/jpeg")})
    body = r.json()
    assert r.status_code == 200 and body["route"] == "review"
    assert body["fields"]["due_date"]["value"] is None and body["fields"]["due_date"]["hard"]
    assert "Due date: we could not find the text this came from" in body["reasons"]


def test_endpoint_rejects_a_non_image_with_our_error_shape():
    from src import app as app_module
    r = TestClient(app_module.app).post("/deadline/photo", files={"image": ("x.txt", b"hello", "text/plain")})
    assert r.status_code == 422 and r.json()["error"]["code"] == "not_an_image"
