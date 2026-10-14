import sys, json
from src.llm import complete

def build_prompt(email):
    return "Analyze the email. Return ONLY a valid JSON object strictly with these keys: 'tone' ('polite', 'neutral', or 'rude'), 'reason' (1 sentence), 'suggested_fix' (1 sentence).\n\nEmail:\n" + email

def parse_response(raw):
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)
    if data.get("tone") not in ["polite", "neutral", "rude"]:
        raise ValueError("Tone must be polite, neutral, or rude")
    return data

def check_email(email, llm=complete):
    email = email.strip()
    if not email: raise ValueError("Email is empty")
    if len(email) > 2000: raise ValueError("Email too long")
    return parse_response(llm(build_prompt(email)))
