import os
from src.tone_checker import check_emails

emails = {
    "G1": {"text": "Send me the report right now. This is completely unacceptable performance.", "expected": "rude"},
    "G2": {"text": "Hi team, thank you for your hard work on this release. Could you please share the latest update when convenient?", "expected": "polite"},
    "G3": {"text": "Send me the file.", "expected": "neutral"}
}
results = []
for tag, data in emails.items():
    try:
        actual = check_email(data["text"]).get("tone")
        status = "PASS" if actual == data["expected"] else "FAIL"
        results.append((tag, data['text'], data['expected'], actual, status))
    except Exception as e:
        print(tag, "error:", e)
        results.append((tag, data['text'], data['expected'], f"ERROR: {type(e).__name__}", "FAIL"))

with open("golden.md", "w", encoding="utf-8") as f:
    f.write("# HW1 Golden Questions\n\n| # | Input Email | Expected | Actual | Result |\n|---|---|---|---|---|\n")
    for r in results: f.write(f"| {r[0]} | `{r[1]}` | {r[2]} | {r[3]} | {r[4]} |\n")
print("golden.md successfully written!")