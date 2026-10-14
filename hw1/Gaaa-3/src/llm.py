import os, time, json, requests
from datetime import datetime, timezone

def complete(prompt):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key: raise ValueError("OPENROUTER_API_KEY is not set")
    model = os.environ.get("OPENROUTER_MODEL", "google/gemini-3.8-flash")
    start = time.time()
    
    payload = {
        "model": model, 
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500
    }
    
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions", 
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, 
        json=payload
    )
    resp.raise_for_status()
    
    latency_ms = int((time.time() - start) * 1000)
    data = resp.json()
    usage = data.get("usage", {})
    p_tok = usage.get("prompt_tokens", 0)
    c_tok = usage.get("completion_tokens", 0)
    cost = (p_tok * 0.75 + c_tok * 3.75) / 1000000
    
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(), 
        "model": model, 
        "prompt_tokens": p_tok, 
        "completion_tokens": c_tok, 
        "latency_ms": latency_ms, 
        "cost_usd": round(cost, 6)
    }
    
    os.makedirs("logs", exist_ok=True)
    with open("logs/usage.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
        
    return data["choices"][0]["message"]["content"]