# AI Two-Pass Safety Layer

A small, self-contained demo of the pattern I use in production to make AI output safe before it reaches a client or a CRM: generate, then validate and correct against a fixed rule set, and hold anything that still fails instead of releasing it.

## Why this exists

When AI writes something a client will read, or writes to a system of record, "usually correct" is not good enough. One off-spec output that reaches a paying client is a real problem. This layer turns a single generation step into a gated pipeline:

1. Generate the content.
2. Validate it against explicit rules: banned phrases, required sections, length, leaked internal fields, unfilled placeholders.
3. If it fails, correct it and re-check.
4. If it still fails after the allowed attempts, hold it for review and never release it.

## Files

- `safety_layer.py` : the full pattern, runnable offline with a built-in sample that intentionally fails, so you can watch it get caught and fixed.

## Run it
