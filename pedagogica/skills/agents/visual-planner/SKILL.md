---
name: visual-planner
version: 0.0.1
category: orchestration
triggers:
  - stage:visual-planner
requires:
  - scene-spec-schema@^0.1.0
  - scene-composition@^0.0.0
  - color-and-typography@^0.1.0
  - pedagogy-cognitive-load@^0.1.0
token_estimate: 3200
tested_against_model: claude-sonnet-4-6
owner: rachit
last_reviewed: 2026-04-20
description: >
  Turns a storyboard scene beat (plus the scene's script when available) into a
  SceneSpec — the scene-DSL the Manim code agent renders. Produces elements,
  animations ordered via a DAG, and leaves camera empty in Phase 1.
---

# Visual Planner agent

## Purpose

Read the scene's beat from `03_storyboard.json` and (when present) the scene's `script.json`, and emit `scenes/scene_NN/spec.json` conforming to `SceneSpec` (see `schemas/src/pedagogica_schemas/scene_spec.py`). This is the **scene DSL**: a small graph of labelled elements and ordered animations that the Manim code agent will turn into Python.

Pedagogy is already decided (storyboard). Code is decided later (Manim codegen). This agent decides **what appears on screen and in what order**.

## Inputs

- `artifacts/<job_id>/03_storyboard.json` — locate the `SceneBeat` whose `scene_id` matches the current scene. Read `beat_type`, `visual_intent`, `learning_objective_id`, `required_skills`.
- `artifacts/<job_id>/scenes/scene_NN/script.json` — optional. When present, its `markers` tell the planner which spoken words anchor which animations.
- `artifacts/<job_id>/02_curriculum.json` — for terminology and the LO the beat serves.
- `artifacts/<job_id>/job_state.json` — for `trace_id`.

## Output

Write `artifacts/<job_id>/scenes/scene_NN/spec.json`. Fields (see `docs/ARCHITECTURE.md` §5.5):

- Trace metadata: `trace_id` copied from job state, fresh `span_id`, `parent_span_id = storyboard.span_id` (or the script's `span_id` if the script fed this call), `timestamp`, `producer = "visual-planner"`, `schema_version = "0.0.1"`.
- `scene_id`: zero-padded; must exactly match the storyboard beat.
- `elements`: list of `SceneElement` (see below).
- `animations`: list of `SceneAnimation` (see below).
- `camera`: **`{}`**. Phase 1 does not emit camera direction.

### `SceneElement`

One per on-screen object. Required keys:

- `id` — dot-namespaced, snake_case segments. First segment is the role: `eq`, `graph`, `axes`, `label`, `arrow`, `shape`, `text`, `img`. Example: `eq.f`, `graph.parabola`, `label.slope_m`.
- `type` — closed set: `math | text | shape | graph | axes | arrow | label | image`. Inventing a new type is a schema change.
- `content` — LaTeX source for `math`; literal string for `text` / `label`; function expression for `graph` (e.g. `"x**2"`); SVG/PNG path for `image`. Empty string `""` for `axes`, `arrow`, `shape` — their geometry lives in `properties`.
- `properties` — free-form dict per type. Conventional keys:
  - `color` — **semantic name** from `color-and-typography` (`primary`, `variable`, `result`, `correct`, `error`, `annotation`). Never a raw hex.
  - `font_size` — Manim integer; typical range 20–48. The layout agent may pass through.
  - `stroke_width` — numeric, for shapes / arrows.
  - `domain` / `x_range` / `y_range` — for graphs and axes.

The layout agent assigns positions and z-order. Do **not** emit `position`, `z_order`, `scale`, `x`, or `y` in `properties`; they'll be ignored, and the layout agent may place the element elsewhere.

### `SceneAnimation`

One per visible motion. Required keys:

- `id` — unique within the scene. Convention: `anim.<verb>.<target>`, e.g. `anim.write.eq_f`, `anim.transform.sec2tan`.
- `op` — closed set: `write | create | transform | fade_in | fade_out | move_to | highlight`. Maps to Manim primitives (see `manim-primitives` when that skill exists).
- `target_ids` — list of element ids that appear in `elements`. Order matters for `transform`: `target_ids[0]` morphs *into* `target_ids[1]`; both must exist.
- `duration_seconds` — the planner's **estimate**. Use the default rates below; the sync agent will overwrite these once TTS returns word timings.
- `run_after` — `null` = starts at scene t=0; otherwise the `id` of a prior animation. The animation starts when that one ends.

The `run_after` graph must be a DAG. One spine of serial animations with occasional short parallel branches is typical; see `scene-spec-schema` for concurrency guidance.

## Duration estimates

| op | default `duration_seconds` |
|---|---|
| `write` | `0.4 × symbol-count` for math; `0.6` for single words. Cap at `2.0`. |
| `create` | `0.6` for shapes; `1.0–1.4` for graphs; `0.5` for axes. |
| `transform` | `0.8–1.6` — longer for bigger morphs. |
| `fade_in` / `fade_out` | `0.5–0.8`. |
| `move_to` | `0.6–1.0`. |
| `highlight` | `0.4–0.8`. |

These are author-intent guesses. The sync agent reconciles them against measured word timings later; do not treat them as final.

## Planning heuristics by beat_type

| `beat_type` | Typical shape |
|---|---|
| `hook` | 1–3 elements, 2–4 animations. One provocative figure or question. Minimal chrome. |
| `define` | 2–5 elements including a display equation + one or two labels. `write` the equation, `fade_in` labels, maybe one `highlight`. |
| `motivate` | 3–6 elements: a concrete instance (graph or figure) plus text. `create` → `highlight` → `write` spine. |
| `example` | 4–8 elements, 6–10 animations. Worked step-by-step: each step is one animation, with `transform` between substitution states. |
| `generalize` | 3–5 elements, usually culminating in a `transform` from specific to general form. |
| `recap` | 2–4 elements; mostly `fade_in`s of thumbnails or summary text. |

Beats whose storyboard `required_skills` includes `"manim-calculus-patterns"` signal a calculus-specific pattern (derivative-as-slope, Riemann sum, epsilon-delta limit). Load that skill when it exists and prefer its canonical element set / naming.

## Using the script's markers (when present)

When `script.json` exists for this scene, it contains `markers` shaped `{word_index, marker_type: "show"|"highlight"|"pause"|"transition", ref: "eq.secant"}`. For each marker:

- The `ref` **must** appear as an element `id` you emit. If the script names `eq.secant`, the spec needs `eq.secant` in `elements`.
- The `marker_type` suggests the animation op:
  - `show` → `write`, `create`, or `fade_in`.
  - `highlight` → `highlight`.
  - `transition` → `transform`, or a `fade_out` → `fade_in` pair.
  - `pause` → no new animation; just a gap.
- The sync agent will align each animation's `start_seconds` to the word. You do not set that here; you only ensure the referenced element exists and an animation targets it.

If the script hasn't been produced yet, plan the scene from `visual_intent` alone. The sync agent will do its best with no markers and larger tolerances.

## Cognitive-load budget

From `pedagogy-cognitive-load`:

- **At most one new concept per 20–30 s.** For a 40 s `example` beat, that's 1–2 concept introductions, not 4.
- **At most 3 simultaneously highlighted elements.** If the beat needs more, serialize.
- **At most 4 active `color-and-typography` semantic slots per scene.** Past that, the colour key becomes the thing being learned.
- **Prefer one spine.** A parallel branch earns its place only when two things genuinely happen at once (e.g. a label fading in while a curve is still being drawn).

## Model

Sonnet 4.6. Opus is reserved for the Manim code agent.

## Validation

After writing the file, the orchestrator will run:

```
uv run pedagogica-tools validate SceneSpec artifacts/<job_id>/scenes/scene_NN/spec.json
```

A non-zero exit is a failure of this agent. You will be re-prompted once with the validator's stderr; a second failure is a hard fail. The validator rejects:

- Unknown fields anywhere (`extra="forbid"`).
- `type` or `op` outside the literal sets.
- Animations whose `target_ids` reference element ids not in `elements` (surface this yourself before emitting — Pydantic's own check is best-effort; cross-reference manually).
- `scene_id` inconsistent with the storyboard beat (the orchestrator cross-checks).

The validator does **not** catch overlapping elements (layout's job), bad pedagogy, cycles in `run_after`, or too many concepts per beat. Self-check those before emitting.

## Example

Input — one `SceneBeat` from `03_storyboard.json`:

```json
{
  "scene_id": "scene_04",
  "beat_type": "example",
  "target_duration_seconds": 40.0,
  "learning_objective_id": "LO2",
  "visual_intent": "secant line sliding toward the tangent as h shrinks on f(x)=x^2",
  "narration_intent": "walk through the limit that turns the secant into the tangent",
  "required_skills": ["manim-calculus-patterns"]
}
```

Output — `scenes/scene_04/spec.json` (abbreviated):

```json
{
  "scene_id": "scene_04",
  "elements": [
    {"id": "axes.main",      "type": "axes",  "content": "",         "properties": {"x_range": [-1, 3], "y_range": [-1, 5], "color": "annotation"}},
    {"id": "graph.parabola", "type": "graph", "content": "x**2",     "properties": {"color": "primary", "domain": [-1, 3]}},
    {"id": "arrow.secant",   "type": "arrow", "content": "",         "properties": {"color": "variable", "stroke_width": 3}},
    {"id": "arrow.tangent",  "type": "arrow", "content": "",         "properties": {"color": "result",   "stroke_width": 3}},
    {"id": "label.h",        "type": "label", "content": "h \\to 0", "properties": {"color": "variable", "font_size": 28}}
  ],
  "animations": [
    {"id": "anim.create.axes",       "op": "create",    "target_ids": ["axes.main"],                     "duration_seconds": 0.5, "run_after": null},
    {"id": "anim.create.parab",      "op": "create",    "target_ids": ["graph.parabola"],                "duration_seconds": 1.2, "run_after": "anim.create.axes"},
    {"id": "anim.write.secant",      "op": "write",     "target_ids": ["arrow.secant"],                  "duration_seconds": 0.9, "run_after": "anim.create.parab"},
    {"id": "anim.fade_in.h",         "op": "fade_in",   "target_ids": ["label.h"],                       "duration_seconds": 0.6, "run_after": "anim.write.secant"},
    {"id": "anim.transform.sec2tan", "op": "transform", "target_ids": ["arrow.secant", "arrow.tangent"], "duration_seconds": 1.6, "run_after": "anim.fade_in.h"}
  ],
  "camera": {}
}
```

`label.h` fades in on the spine (not in parallel) because the scene is already busy while the parabola is being drawn. The `transform` morphs `arrow.secant` into `arrow.tangent`; both elements must exist.

## Anti-patterns

- **Raw hex colours in `properties.color`.** Use semantic names; the Manim codegen resolves them via `color-and-typography`.
- **Emitting `position`, `scale`, `z_order`, or layout-ish keys.** That is the layout agent's output.
- **Populating `camera`.** It will be dropped on the floor; worse, it implies camera direction exists.
- **New `type` or `op` values.** Closed sets. A need for a new one is a schema change, not a local freedom.
- **Dangling `target_ids`.** Every id in an animation must appear in `elements`. Cross-reference before emitting.
- **Renaming ids the script references.** If the script's `ref` is `eq.secant`, emit `eq.secant`; don't prettify to `equation.secant_line`.
- **More than ~12 animations for one beat.** That's a signal the storyboard overfilled the beat. Flag rather than cram.
- **Rainbow-every-term colouring.** One semantic role per element per scene; see `color-and-typography`.
- **Treating `duration_seconds` as authoritative.** Sync will overwrite them. Don't hardcode narration timing here.

## Changelog

- **0.0.1** (2026-04-20) — initial Phase 1 draft. Consumes storyboard (and optional script); emits `SceneSpec` with `camera = {}`. `manim-calculus-patterns` is loaded conditionally when the storyboard beat lists it in `required_skills`.
