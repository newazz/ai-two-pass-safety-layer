# AI Two-Pass Safety Layer

A small, self-contained demo of the pattern I use in production to make AI output safe before it reaches a client or a CRM: generate, then validate and correct against a fixed rule set, and hold anything that still fails instead of releasing it.

## Why this exists

When AI writes something a client will read, or writes to a system of record, “usually correct” is not good enough. One off-spec output that reaches a paying client is a real problem. This layer turns a single generation step into a gated pipeline:

Generate the content.
Validate it against explicit rules: banned phrases, required sections, length, leaked internal fields, unfilled placeholders.
If it fails, correct it and re-check.
If it still fails after the allowed attempts, hold it for review and never release it.

## Files

safety_layer.py : the full pattern, runnable offline with a built-in sample that intentionally fails, so you can watch it get caught and fixed.

## Run it

```
python safety_layer.py
```

No API key needed for the demo. It ships with a sample draft that breaks several rules, runs it through the layer, and prints the cleaned result and the gate decision.

## Live mode (optional)

Set ANTHROPIC_API_KEY and the generate and correct steps call Claude instead of the offline stubs:

```
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
python safety_layer.py
```

## How it maps to production

In a real build the validate step holds the client’s own rules (privacy boundaries, tone, required content), and the hold path routes failures to a human review queue instead of delivery. The principle stays the same: nothing off-spec is ever released automatically.

Built by Newaz, FormLogic Studio (https://formlogicstudio.com). Generic sample, no client data.
