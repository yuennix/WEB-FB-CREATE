---
name: Facebook brotli encoding bug
description: Facebook sends brotli-compressed responses when br is in Accept-Encoding, but requests can't decode brotli — causing garbled HTML and failed token extraction.
---

## Rule
Never include `br` in `Accept-Encoding` when making requests to Facebook with the `requests` library.

Use: `'Accept-Encoding': 'gzip, deflate'`

**Why:** Facebook respects the `br` encoding preference and returns brotli-compressed responses. Python `requests` has no built-in brotli decoder, so `.text` returns garbled binary. All regex token extractions (LSD, jazoest, revision, etc.) fail silently — the code sees an empty/garbage HTML body and logs "Could not load reg page". Installing `brotli` package would also fix it, but omitting `br` is simpler and has no downside.

**How to apply:** Any GET request to `www.facebook.com` or `m.facebook.com` in this codebase must strip `br` from Accept-Encoding. Check all headers dicts in `app.py` and `main.py`.
