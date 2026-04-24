---
name: storyboard
version: 0.0.1
category: orchestration
triggers:
  - stage:storyboard
requires: []
token_estimate: 3600
tested_against_model: claude-sonnet-4-6
owner: rachit
last_reviewed: 2026-04-20
description: >
  Turns a CurriculumPlan into the scene-by-scene master plan (Storyboard).
  Every downstream agent reads this as the single source of truth.
---

# Storyboard agent

## Purpose

Read `01_intake.json` + `02_curriculum.json` and emit `03_storyboard.json` (`Storyboard` — see `schemas/src/pedagogica_schemas/storyboard.py`). This file is the **master plan**: every later agent (script, visual-planner, layout, manim-code, tts, sync, editor) references it.

## Inputs

- `artifacts/<job_id>/01_intake.json`
- `artifacts/<job_id>/02_curriculum.json`
- `artifacts/<job_id>/job_state.json` — for trace metadata.

## Output

Write `artifacts/<job_id>/03_storyboard.json`. Fields:

- Trace metadata: `trace_id` copied, fresh `span_id`, `parent_span_id = curriculum.span_id`, `timestamp`, `producer = "storyboard"`, `schema_version = "0.1.0"` (matches `Storyboard` default).
- `topic`: copy from intake.
- `total_duration_seconds`: equal to `intake.target_length_seconds` (float). The sum of scene durations must be within ±0.5s of this (schema-enforced — see `Storyboard._scenes_consistent`).
- `scenes`: **4–10** `SceneBeat`s. Each:
  - `scene_id`: zero-padded, consecutive starting at `"scene_01"`.
  - `beat_type`: one of `hook | define | motivate | example | generalize | recap`. At most one `hook` (first scene if present); at most one `recap` (last scene if present).
  - `target_duration_seconds`: positive float. Use the duration guidance below.
  - `learning_objective_id`: the LO this scene serves (e.g. `"LO2"`) or `null` for `hook` / `recap`.
  - `visual_intent`: **one** concise prose sentence describing what the viewer sees. Not a Manim spec, not code.
  - `narration_intent`: **one** concise prose sentence describing what the narrator says. Not the final script.
  - `required_skills`: list of `chalk-*-patterns` knowledge-skill names the chalk-code agent should load. E.g. `["chalk-calculus-patterns"]`, `["chalk-circuit-patterns"]`, `["chalk-physics-patterns"]`, `["chalk-chemistry-patterns"]`, `["chalk-coding-patterns"]`, `["chalk-graph-patterns"]`. `hook` / `recap` may be empty.
- `palette`: **Phase 1 fixed preset** — copy exactly:
  ```json
  {"bg": "#0b0f1a", "fg": "#ffffff", "accent": "#4da3ff", "muted": "#7a8599", "highlight": "#ffcf5c"}
  ```
- `voice_id`: **Phase 1 fixed default** — `"21m00Tcm4TlvDq8ikWAM"` (ElevenLabs "Rachel").

## Duration guidance

| beat_type | typical duration |
|---|---|
| hook | 10–20s |
| define | 20–40s |
| motivate | 20–40s |
| example | 30–60s |
| generalize | 20–40s |
| recap | 15–25s |

These are guidelines; the only hard constraint is that the scene total is within ±0.5s of `total_duration_seconds`.

## Depth budget — cap LOs per video

Every extra learning objective turns a video from an explanation into a firehose. Cap aggressively:

| `target_length_seconds` | Max LOs covered in depth | Extra LOs may be *named* only |
|---|---|---|
| 60–120 | 1 | 0 |
| 120–240 (Phase-1 sweet spot) | 1 (sometimes 2 if tightly linked) | 1 more, as a teaser in the recap |
| 240–360 | 2 | 1 |
| 360–600 | 3 | 1 |

"In depth" means: has its own `define` scene + its own `example` scene. A mentioned-but-not-taught LO does NOT count — if the curriculum lists 3 LOs but the video only covers 1, that's fine; drop the other two from the scene list or name them in the recap as "next video" hooks.

If you receive a `CurriculumPlan` with more LOs than this budget allows, **pick the subset** that best serves the hook question. Don't try to fit all of them. Cramming LOs at the budget limit will produce dense narration that reads like a textbook summary, not an explainer.

> **Validator:** `pedagogica-tools check-storyboard <storyboard.json>` enforces this cap after generation. Exceeding the cap triggers a re-prompt; second failure halts the stage.

Pick-rule in priority order:
1. The LO that directly answers the hook's question.
2. The LO whose prerequisites are already carried by the audience level.
3. The LO with the cleanest single visual (graph, diagram, animation).
Skip the rest with a one-line recap mention: "We've only scratched the surface — next time: …".

## Sequencing rules

- Every LO appears in at least one `define` or `motivate` beat before any `example` beat that depends on it (follow `curriculum.sequence` transitively).
- `hook` (if present) is `scene_01`; `recap` (if present) is the final scene.
- `generalize` beats come after their associated `example`.
- Prefer alternation: `define` → `example` → `generalize` → `recap` beats a wall of `define`s.

## Validation rules enforced by the schema

The validator rejects:

- duplicate or non-consecutive `scene_id`s.
- more than one `hook` or `recap`.
- `hook` not at `scene_01`, or `recap` not at the final scene.
- scene durations whose sum is more than 0.5s off `total_duration_seconds`.
- missing `visual_intent` / `narration_intent`.
- unknown fields (`extra="forbid"`).

Fix and re-emit if the validator complains.

## Example (abbreviated)

Input (`02_curriculum.json`): 3 LOs on the chain rule, sequence `["LO1", "LO2", "LO3"]`, `target_length_seconds = 180`.

Output (`03_storyboard.json` — abbreviated):

```json
{
  "topic": "chain rule",
  "total_duration_seconds": 180.0,
  "scenes": [
    {"scene_id": "scene_01", "beat_type": "hook", "target_duration_seconds": 15.0,
     "learning_objective_id": null,
     "visual_intent": "a bare curve sin(x^2) traced out with an unknown slope marker",
     "narration_intent": "pose: how fast is this changing at x=1?",
     "required_skills": []},
    {"scene_id": "scene_02", "beat_type": "define", "target_duration_seconds": 45.0,
     "learning_objective_id": "LO1",
     "visual_intent": "decompose sin(x^2) into inner u=x^2 and outer sin(u) with color-coded arrows",
     "narration_intent": "introduce composition and name the inner/outer pieces",
     "required_skills": ["manim-calculus-patterns"]},
    {"scene_id": "scene_03", "beat_type": "example", "target_duration_seconds": 60.0,
     "learning_objective_id": "LO2",
     "visual_intent": "step-by-step differentiation of sin(x^2), outer-then-inner, with the product appearing",
     "narration_intent": "apply the chain rule to sin(x^2), narrating each factor",
     "required_skills": ["manim-calculus-patterns"]},
    {"scene_id": "scene_04", "beat_type": "generalize", "target_duration_seconds": 40.0,
     "learning_objective_id": "LO3",
     "visual_intent": "two local slope gauges multiplying to produce the outer slope",
     "narration_intent": "recast the result as multiplication of local rates",
     "required_skills": ["manim-calculus-patterns"]},
    {"scene_id": "scene_05", "beat_type": "recap", "target_duration_seconds": 20.0,
     "learning_objective_id": null,
     "visual_intent": "the three panels from earlier shrink to thumbnails across the bottom",
     "narration_intent": "summarize in two sentences",
     "required_skills": []}
  ],
  "palette": {"bg": "#0b0f1a", "fg": "#ffffff", "accent": "#4da3ff", "muted": "#7a8599", "highlight": "#ffcf5c"},
  "voice_id": "21m00Tcm4TlvDq8ikWAM"
}
```

## Anti-patterns

- Do not embed Manim code or LaTeX inside `visual_intent`. That's the visual-planner and manim-code agents' job.
- Do not write full narration. That's the script agent's job.
- Do not invent palette colors — Phase 1 uses the fixed preset verbatim.
- Do not produce more than 10 scenes for a Phase 1 target length.
- Do not drop the recap unless the total is < 90s.
