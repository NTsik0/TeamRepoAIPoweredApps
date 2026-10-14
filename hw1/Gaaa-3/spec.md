# Email Tone Checker (HW1, Gaaa-3)

## Run commands
    cd hw1/Gaaa-3
    pip install requests pytest
    python -m pytest                          # tests, no API key needed
    export OPENROUTER_API_KEY="..."           # your own key, never committed
    export OPENROUTER_MODEL="..."             # a model id from openrouter.ai/models
    python src/tone_checker.py email.txt      # run on a real email

## What it does
Reads one email from a text file. Asks an LLM (via OpenRouter) to rate its
tone and suggest one fix. Prints the result.

## Input
- A plain text file with one email (max 2,000 characters).
- Empty file or too long: exit with a clear error, no API call.

## Output (JSON printed to the terminal)
    {"tone": "polite" | "neutral" | "rude",
     "reason": "one sentence",
     "suggested_fix": "one rewritten sentence"}

## Design
- build_prompt(email): builds the instruction, asks for JSON only.
- call_llm(prompt): the only function that touches the network.
- parse_response(raw): checks the JSON, rejects unknown tone labels.
- check_email(email, llm=call_llm): ties them together. The llm argument
  lets tests pass in a fake.

## Tests (no API key)
- valid JSON is parsed correctly
- invalid JSON raises a clear error
- tone outside polite/neutral/rude is rejected
- empty and too-long emails are rejected before any call
- check_email works end to end with a fake llm

## Golden questions (real runs, my own key)
1. Clearly rude email -> expect "rude"
2. Clearly polite email -> expect "polite"
3. Ambiguous, short email ("Send me the file.") -> expect "neutral"
   or "rude", and the fix should add politeness

## Out of scope
No web UI, no multiple emails, no saving history.
