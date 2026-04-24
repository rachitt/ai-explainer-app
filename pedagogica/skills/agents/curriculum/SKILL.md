---
name: curriculum
version: 0.0.1
category: orchestration
triggers:
  - stage:curriculum
requires: []
token_estimate: 2400
tested_against_model: claude-sonnet-4-6
owner: rachit
last_reviewed: 2026-04-20
description: >
  Expands a normalized IntakeResult into a pedagogical plan — learning
  objectives, prerequisites, worked examples, and a topological ordering.
---

# Curriculum agent

## Purpose

Read `01_intake.json` and emit `02_curriculum.json` conforming to `CurriculumPlan` (see `schemas/src/pedagogica_schemas/curriculum.py`). This is the first real reasoning stage — it decides **what to teach, in what order, building on what**.

## Inputs

- `artifacts/<job_id>/01_intake.json` — already validated.
- `artifacts/<job_id>/job_state.json` — inherit `trace_id`.

## Output

Write `artifacts/<job_id>/02_curriculum.json`. Fields:

- Trace metadata: `trace_id` copied from job state, fresh `span_id`, `parent_span_id = intake.span_id`, `timestamp`, `producer = "curriculum"`, `schema_version = "0.0.1"`.
- `topic`: copy from `intake.topic`.
- `objectives`: **2–4** `LearningObjective`s. Each:
  - `id`: `"LO1"`, `"LO2"`, … (regex `^LO\d+$`).
  - `text`: starts with an action verb ("understand …", "compute …", "interpret …"). One sentence.
  - `prerequisites`: list of **other LO ids** that must be taught first (within this plan). Empty list if none.
- `prerequisites`: list of short strings naming **prior knowledge the viewer brings in** (e.g. `["limits", "function notation"]`). These are **not** LO ids — they are external prior knowledge.
- `misconceptions`: **Phase 1: empty list `[]`**. Preempting misconceptions ships Phase 2 (see `docs/ROADMAP.md`).
- `worked_examples`: 1–3 short prose summaries of examples the storyboard will elaborate. One sentence each. Do **not** write full narration or code.
- `sequence`: ordered list of LO ids. Must be a permutation of `objectives[*].id` that respects every `prerequisites` edge.

## Models and knowledge

Sonnet 4.6. Load all four `requires` skills. Budget ~10k input tokens once skill content is in context.

## Decision heuristics

- **Ratio of LOs to length:** ~1 LO per 60 seconds of video. 120s → 2 LOs; 180s → 2–3 LOs; 240s → 3–4 LOs.
- **The hook question is the anchor.** `01_intake.json.hook_question` is your pedagogical anchor. The LO list you produce must collectively be capable of answering it. If the hook question demands content outside the domain, trim the topic back in intake instead of expanding curriculum to chase it.
- **Concrete before abstract.** An intuitive / visual LO comes before a formal LO that rests on it. Prerequisites should reflect this ("LO2 depends on LO1" when LO2 formalizes what LO1 visualized).
- **Single threaded example preferred.** Where possible, a single worked example should recur across LOs — reuse lowers cognitive load (`pedagogy-cognitive-load`).
- **External prerequisites stay in `prerequisites`, not objectives.** If the viewer needs to know limits, say so under `prerequisites`; don't create an LO to re-teach limits inside a 180s video.
- **Do not restate the topic as an objective.** "understand the chain rule" is not an LO for a video on the chain rule — it's the topic. LOs decompose the topic into teachable chunks.

## Validation rules enforced by the schema

The validator will reject your output if:

- `sequence` is not a permutation of objective ids.
- An LO's `prerequisites` references an id that's not in `objectives`.
- `sequence` places an LO before one of its prerequisites.
- Any unknown field is present (`extra="forbid"`).

Fix and re-emit if the validator complains.

## Example

Input (`01_intake.json`):

```json
{"topic": "chain rule", "domain": "calculus", "audience_level": "undergrad",
 "target_length_seconds": 180, ...}
```

Output (`02_curriculum.json` — abbreviated):

```json
{
  "topic": "chain rule",
  "objectives": [
    {"id": "LO1", "text": "recognize when a function is a composition", "prerequisites": []},
    {"id": "LO2", "text": "apply the chain rule to compute derivatives of compositions", "prerequisites": ["LO1"]},
    {"id": "LO3", "text": "interpret the chain rule as multiplication of local rates", "prerequisites": ["LO2"]}
  ],
  "prerequisites": ["function notation", "derivative of elementary functions"],
  "misconceptions": [],
  "worked_examples": ["differentiate sin(x^2) step by step, highlighting the inner/outer decomposition"],
  "sequence": ["LO1", "LO2", "LO3"]
}
```

## Anti-patterns

- Do not produce 8 LOs for a 180s video. You will blow the cognitive-load budget in storyboard.
- Do not leave `sequence` empty or mis-ordered. The validator will reject it.
- Do not use misconceptions in Phase 1 even if tempting — the handling skill isn't wired yet.
- Do not restate the prompt as an objective.
