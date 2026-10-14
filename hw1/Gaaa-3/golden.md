# HW1 Golden Questions

| # | Input Email | Expected | Actual | Result |
|---|---|---|---|---|
| G1 | `Send me the report right now. This is completely unacceptable performance.` | rude | ERROR: HTTPError | FAIL |
| G2 | `Hi team, thank you for your hard work on this release. Could you please share the latest update when convenient?` | polite | ERROR: HTTPError | FAIL |
| G3 | `Send me the file.` | neutral | ERROR: HTTPError | FAIL |
