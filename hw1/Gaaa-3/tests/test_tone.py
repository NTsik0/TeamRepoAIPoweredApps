import pytest
from src.tone_checker import parse_response, check_email

def test_parse_valid():
    assert parse_response('{"tone": "polite", "reason": "Good", "suggested_fix": "None"}')["tone"] == "polite"

def test_parse_invalid():
    with pytest.raises(ValueError): parse_response("Not json")
    with pytest.raises(ValueError): parse_response('{"tone": "angry", "reason": "", "suggested_fix": ""}')

def test_check_email_bounds():
    with pytest.raises(ValueError): check_email("   ")
    with pytest.raises(ValueError): check_email("a" * 2001)

def test_check_email_e2e():
    def fake_llm(p): return '{"tone": "rude", "reason": "Short", "suggested_fix": "Fix"}'
    assert check_email("Do it now", llm=fake_llm)["tone"] == "rude"
