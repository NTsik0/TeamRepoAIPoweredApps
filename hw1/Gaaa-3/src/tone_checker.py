import os
import sys
import json
import requests

def build_prompt(email):
    return (
        "Analyze the following email. Return ONLY a valid JSON object with strictly these keys: "
        "'tone' (must be 'polite', 'neutral', or 'rude'), 'reason' (one sentence), "
        "and 'suggested_fix' (one rewritten sentence).\n\n"
        f"Email:\n${email}"
    )

def call_llm(prompt):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("OPENROUTER_MODEL", "google/gemini-3.8-flash")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set")
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    resp.raise_for_status()
    
    content = resp.json(")["choices"][0]["message"]["content"].strip()
    if content.startswith("```jon"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()

def parse_response(raw):
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON returned by LLM")
    
    if data.get("tone") not in ["polite", "neutral", "rude"]:
        raise ValueError("Tone must be polite, neutral, or rude")
    return data

def check_email(email, llm=call_llm):
    email = email.strip()
    if not email:
        raise ValueError("Email is empty")
    if len(email) > 2000:
        raise ValueError("Email too long")
    
    prompt = build_prompt(email)
    raw_response = llm(prompt)
    return parse_response(raw_response)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/tone_checker.py <email_file.txt>")
        sys.exit(1)
    
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        content = f.read()
    
    try:
        result = check_email(content)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error:"{s}")
        sys.exit(1)
