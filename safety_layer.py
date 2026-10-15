"""
Two-pass AI safety layer (demo)

Pattern: generate -> validate -> correct -> re-validate -> release or hold.
Runnable offline with a built-in sample draft that intentionally breaks
several rules, so you can see the layer catch and fix them. Set
ANTHROPIC_API_KEY to run the generate and correct steps through Claude.

Author: Newaz, FormLogic Studio
"""

import os
import re

# ---- Rule set ---------------------------------------------------------------

BANNED_PHRASES = ["guaranteed cure", "100% success", "medical advice"]
REQUIRED_SECTIONS = ["Summary", "Next steps"]
MAX_CHARS = 1200
PLACEHOLDER_PATTERN = re.compile(r"\{\{.*?\}\}|\[TODO\]|XXXX", re.IGNORECASE)
INTERNAL_FIELD_PATTERN = re.compile(r"internal_id", re.IGNORECASE)


def validate(text):
    """Return a list of rule violations. Empty list means the text is clean."""
    violations = []
    lowered = text.lower()

    for phrase in BANNED_PHRASES:
        if phrase.lower() in lowered:
            violations.append(f"banned_phrase: {phrase!r}")

    for section in REQUIRED_SECTIONS:
        if section.lower() not in lowered:
            violations.append(f"missing_section: {section!r}")

    if len(text) > MAX_CHARS:
        violations.append(f"too_long: {len(text)} > {MAX_CHARS}")

    if PLACEHOLDER_PATTERN.search(text):
        violations.append("unfilled_placeholder")

    if INTERNAL_FIELD_PATTERN.search(text):
        violations.append("leaked_internal_field")

    return violations


# ---- Generate and correct ---------------------------------------------------

def _has_claude():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _demo_draft(intake):
    """Offline sample that deliberately breaks rules, for the demo."""
    return (
        f"Hello {intake['first_name']},\n\n"
        "Thank you for your submission. This plan is a guaranteed cure "
        "for your situation and offers 100% success.\n"
        "internal_id: 4471\n"
        "We will be in touch soon. [TODO]\n"
    )


def generate(intake):
    if _has_claude():
        return _claude_generate(intake)
    return _demo_draft(intake)


def correct(text, violations):
    if _has_claude():
        return _claude_correct(text, violations)
    return _deterministic_correct(text)


def _deterministic_correct(text):
    """Offline correction so the demo runs without an API key."""
    clean_lines = []
    for line in text.splitlines():
        low = line.lower()
        if any(p.lower() in low for p in BANNED_PHRASES):
            continue
        if INTERNAL_FIELD_PATTERN.search(line):
            continue
        clean_lines.append(line)
    text = "\n".join(clean_lines)

    text = PLACEHOLDER_PATTERN.sub("", text)

    for section in REQUIRED_SECTIONS:
        if section.lower() not in text.lower():
            text += f"\n\n{section}\n- (to be completed by the system)"

    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    return text.strip() + "\n"


# ---- Claude-backed steps (used only when ANTHROPIC_API_KEY is set) ----------

def _claude_generate(intake):
    from anthropic import Anthropic
    client = Anthropic()
    prompt = (
        "Write a short, warm welcome note for "
        f"{intake['first_name']}. Include a 'Summary' section and a "
        "'Next steps' section. Do not give medical advice or make "
        "guarantees. Keep it under 1000 characters."
    )
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _claude_correct(text, violations):
    from anthropic import Anthropic
    client = Anthropic()
    prompt = (
        "Rewrite the text below so it fixes every listed problem and "
        "nothing else. Keep the tone and the useful content.\n\n"
        "Problems:\n- " + "\n- ".join(violations) + "\n\n"
        f"Text:\n{text}"
    )
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ---- Orchestration ----------------------------------------------------------

def run(intake, max_attempts=2):
    """Generate, then validate and correct up to max_attempts.
    Release only if clean, otherwise hold for review."""
    draft = generate(intake)

    for attempt in range(1, max_attempts + 1):
        violations = validate(draft)
        if not violations:
            return {"status": "released", "attempts": attempt - 1, "text": draft}
        draft = correct(draft, violations)

    remaining = validate(draft)
    if remaining:
        return {"status": "held", "violations": remaining, "text": draft}
    return {"status": "released", "attempts": max_attempts, "text": draft}


if __name__ == "__main__":
    sample_intake = {"first_name": "Alex"}
    result = run(sample_intake)

    print("Gate decision:", result["status"].upper())
    if result["status"] == "held":
        print("Unresolved violations:", result["violations"])
    print("-" * 40)
    print(result["text"])
