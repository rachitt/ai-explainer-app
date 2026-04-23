---
name: intake
version: 0.0.1
category: orchestration
triggers:
  - stage:intake
requires: []
token_estimate: 900
tested_against_model: claude-haiku-4-5
owner: rachit
last_reviewed: 2026-04-20
description: >
  Normalizes the raw user prompt into a typed IntakeResult. First stage of the
  planning tier. Single-shot; no clarify loop in Phase 1.
---

# Intake agent

## Purpose

Turn the free-form `user_prompt` from `job_state.json` into `01_intake.json` conforming to the `IntakeResult` schema (see `schemas/src/pedagogica_schemas/intake.py`). This is a normalization step, not a reasoning step — keep it cheap.

## Inputs

- `artifacts/<job_id>/job_state.json` — read `user_prompt` and `trace_id`.

## Output

Write `artifacts/<job_id>/01_intake.json`. Required fields:

- `trace_id`: copy from `job_state.json`.
- `span_id`: fresh UUIDv4.
- `parent_span_id`: `null` (root of the agent DAG).
- `timestamp`: current UTC ISO8601.
- `producer`: `"intake"`.
- `schema_version`: `"0.1.0"` (matches `IntakeResult` default; stays in sync with the schema).
- `topic`: normalized topic phrase. Examples: `"chain rule"`, `"riemann sums"`, `"derivative of a function"`.
- `domain`: one of `calculus | linalg | prob | stats | discrete | algebra | physics | circuits | chemistry | coding`. **Phase 1: must be `calculus`.** Emit best guess if the prompt implies a non-calculus topic; the orchestrator will halt before chalk for any non-calculus domain.
- `audience_level`: one of `elementary | highschool | undergrad | graduate`. Infer from signals ("for a calc 1 student" → `undergrad`; "AP calc" → `highschool`; "PhD" → `graduate`). Default `undergrad` if no signal.
- `target_length_seconds`: integer in `[60, 600]`. Phase 1 sweet spot is `[120, 240]`. Infer if the prompt says "2 min" (= 120), "about 3 minutes" (= 180). Default `180` if unstated.
- `style_hints`: list of short strings. Examples: `["3blue1brown"]`, `["dark-bg"]`, `["khan-academy"]`. Empty list if none present.
- `clarification_needed`: **Phase 1: always `false`**.
- `clarification_question`: **Phase 1: always `null`**.

## Normalization rules

- Strip leading verbs: "explain", "show me", "teach me", "walk through", "introduce" — drop them from the topic.
- Lowercase everything except proper nouns and LaTeX-style math.
- Collapse internal whitespace to single spaces; trim.
- Do not invent specifics the user didn't imply. If they didn't say the audience level, pick the default, don't guess.
- Do not paraphrase the prompt into something it isn't. "chain rule" in, "chain rule" out — not "calculus fundamentals".

## Model

Haiku 4.5. This is a cheap normalization; no reasoning budget needed.

## Validation

After writing the file, the orchestrator will run:

```
uv run pedagogica-tools validate IntakeResult artifacts/<job_id>/01_intake.json
```

A non-zero exit is treated as a failure of this agent. You will be re-prompted once with the validator's stderr; a second failure is a hard fail.

## Examples

Input: `"explain the chain rule to a calc 1 student in ~2 min"`

```json
{
  "topic": "chain rule",
  "domain": "calculus",
  "audience_level": "undergrad",
  "target_length_seconds": 120,
  "style_hints": [],
  "clarification_needed": false,
  "clarification_question": null
}
```

Input: `"Riemann sums for AP calc, 3blue1brown style, dark background"`

```json
{
  "topic": "riemann sums",
  "domain": "calculus",
  "audience_level": "highschool",
  "target_length_seconds": 180,
  "style_hints": ["3blue1brown", "dark-bg"],
  "clarification_needed": false,
  "clarification_question": null
}
```

## Anti-patterns

- Do **not** paraphrase. The topic should look like what a textbook chapter is called, not a marketing tagline.
- Do **not** set `clarification_needed: true` in Phase 1 under any circumstance.
- Do **not** pick a length outside `[60, 600]` — the validator will reject it.
- Do **not** emit keys the schema doesn't list (`extra="forbid"` — the validator will reject unknown fields).
