---
name: scene-spec-schema
version: 0.1.0
category: manim
triggers:
  - stage:visual-planner
  - stage:layout
  - stage:manim-code
  - stage:manim-repair
  - stage:sync
  - any_agent_touching_scene_spec
requires: []
token_estimate: 1800
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Canonical reference for the SceneSpec contract — the scene-DSL that the visual
  planner emits and every downstream agent (layout, Manim codegen, repair, sync)
  reads. Covers element types, animation ops, id conventions, DAG ordering rules,
  and the camera field's intentional emptiness in Phase 1. Points at
  schemas/src/pedagogica_schemas/scene_spec.py as the source of truth.
---

# scene-spec-schema

## Purpose

`SceneSpec` is the single contract that decouples pedagogical planning from rendering. The visual planner writes it; the Manim-code agent reads it and turns it into Python; the sync agent reads it and aligns timings against narration. If agents disagree on what the schema means, the pipeline produces scenes that don't compose. This skill is how every scene-spec-touching agent agrees.

It is a **reference** skill: short, dense, no embedded opinions. Pedagogy and visual taste live elsewhere (`scene-composition`, `manim-calculus-patterns`, etc.). Here you only learn what fields exist, what values are legal, and the ordering rules the schema does not express.

## When to load

- Visual planner, layout, Manim codegen, Manim repair, and sync — **always**.
- Curriculum / storyboard / script agents — **not needed**; they don't touch scene specs.
- When a compile error says the generated code referenced an element id that isn't in the spec — load this + `manim-debugging`.

## Source of truth

The Pydantic models live in `schemas/src/pedagogica_schemas/scene_spec.py`. That file is authoritative: if it disagrees with this skill, the file wins and this skill is wrong (bump version and fix). Skills reference schemas; they do not own them. See `docs/SKILLS.md` §9.

## Core content

### Top-level `SceneSpec`

| Field | Type | Notes |
|---|---|---|
| `scene_id` | `str` | Zero-padded, matches the storyboard entry — `"scene_01"` … `"scene_12"`. |
| `elements` | `list[SceneElement]` | What's on screen. Order doesn't imply z-order (that comes from layout). |
| `animations` | `list[SceneAnimation]` | How the elements enter / change / leave. DAG via `run_after`. |
| `camera` | `dict[str, Any]` | Empty `{}` in Phase 1. Reserved for `{focus_id, zoom, pan_path_ids}` later. |

All `SceneSpec`s inherit `BaseMessage` (see `schemas/src/pedagogica_schemas/base.py`): `trace_id`, `span_id`, `timestamp`, `producer`, `schema_version`. Don't forge these — the agent emitting the message fills them in.

### `SceneElement`

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Dot-namespaced. See id conventions below. |
| `type` | one of `math`, `text`, `shape`, `graph`, `axes`, `arrow`, `label`, `image` | Closed set. No new types without a schema change. |
| `content` | `str` | LaTeX source for `math`; literal string for `text`/`label`; function expression for `graph` (`"x**2"`); SVG/PNG path for `image`. |
| `properties` | `dict[str, Any]` | Free-form per type. Common keys: `color` (semantic name from `color-and-typography`), `stroke_width`, `font_size`, `domain` (for `graph`). |

### `SceneAnimation`

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Unique within the scene. Convention: `"anim.<verb>.<target>"`, e.g. `"anim.write.eq_f"`. |
| `op` | one of `write`, `create`, `transform`, `fade_in`, `fade_out`, `move_to`, `highlight` | Maps to Manim primitives; see `manim-primitives`. |
| `target_ids` | `list[str]` | Element ids. Every id here must appear in `elements`. Order matters for `transform`: `target_ids[0]` morphs *into* `target_ids[1]`. |
| `duration_seconds` | `float` | Planner's best guess. Sync agent overrides; don't treat it as final. Typical: 0.5–2.0. |
| `run_after` | `str \| None` | `None` = starts at scene t=0. Otherwise the `id` of a prior animation; this animation starts when that one ends. |

The implicit graph formed by `run_after` must be a DAG. One-way time, no cycles. A node can be `run_after` another that was started independently; that's how you get parallel tracks.

### Id conventions

- **Dot-namespaced, snake_case segments**: `eq.f`, `graph.parabola`, `label.slope_m`, `anim.write.eq_f`.
- **First segment is the role**: `eq`, `graph`, `axes`, `label`, `arrow`, `shape`, `text`, `img`, `anim`.
- **Refer only to ids that exist in the same `SceneSpec`.** Cross-scene references are not supported in Phase 1 — each scene stands alone.
- **Stable across edits.** If a scene regenerates (Phase 2), keeping ids stable lets sync and critic diffs be meaningful. Don't rename just to rename.

### Ordering and concurrency

- `run_after: None` animations start at t=0 in parallel. Use this sparingly — it burns cognitive load (`pedagogy-cognitive-load`).
- Chains of `run_after` form the spine of the scene. A typical calculus scene has 6–12 animations in a mostly linear chain with 1–2 short parallel branches (e.g. a label fading in while a curve is being drawn).
- Total scene duration ≈ longest path through the DAG + any `wait_after` the sync plan inserts. The planner's `duration_seconds` sum is a lower bound, not the final number.

### Camera in Phase 1

`camera = {}`. The entire scene is framed by Manim's default 14×8 coordinate window. Don't emit `zoom`, `pan`, or `focus` fields — the Manim codegen won't honour them, and the repair loop has no skill for camera work until Phase 3.

## Examples

### Minimal valid spec (a label fades in)

```json
{
  "scene_id": "scene_02",
  "elements": [
    {"id": "label.intro", "type": "text", "content": "The derivative", "properties": {"color": "primary", "font_size": 48}}
  ],
  "animations": [
    {"id": "anim.fade_in.intro", "op": "fade_in", "target_ids": ["label.intro"], "duration_seconds": 0.8, "run_after": null}
  ],
  "camera": {}
}
```

### Typical calculus beat (secant → tangent)

```json
{
  "scene_id": "scene_04",
  "elements": [
    {"id": "axes.main", "type": "axes", "content": "", "properties": {"x_range": [-1, 3], "y_range": [-1, 5]}},
    {"id": "graph.parabola", "type": "graph", "content": "x**2", "properties": {"color": "primary", "domain": [-1, 3]}},
    {"id": "arrow.secant", "type": "arrow", "content": "", "properties": {"color": "accent_blue"}},
    {"id": "arrow.tangent", "type": "arrow", "content": "", "properties": {"color": "accent_yellow"}}
  ],
  "animations": [
    {"id": "anim.create.axes",    "op": "create",    "target_ids": ["axes.main"],                         "duration_seconds": 0.6, "run_after": null},
    {"id": "anim.create.parab",   "op": "create",    "target_ids": ["graph.parabola"],                    "duration_seconds": 1.2, "run_after": "anim.create.axes"},
    {"id": "anim.write.secant",   "op": "write",     "target_ids": ["arrow.secant"],                      "duration_seconds": 0.9, "run_after": "anim.create.parab"},
    {"id": "anim.transform.sec2tan", "op": "transform", "target_ids": ["arrow.secant", "arrow.tangent"], "duration_seconds": 1.6, "run_after": "anim.write.secant"}
  ],
  "camera": {}
}
```

Note: `transform` morphs `arrow.secant` *into* `arrow.tangent`. Both must appear in `elements`; after the transform the secant is gone.

## Gotchas / anti-patterns

- **Inventing new `type` or `op` values.** The closed sets are in the Pydantic `Literal`s. If you think you need a new one, that's a schema change (major version), not an inline freedom.
- **Dangling `target_ids`.** Every id in an animation's `target_ids` must appear in `elements`. The validator catches this, but the Manim-code agent is more helpful when it doesn't have to.
- **Cycles in `run_after`.** The validator should reject them; if you hand-edit a spec, don't introduce them.
- **Treating `duration_seconds` as authoritative.** It's the planner's guess. The sync agent will replace it. Don't hardcode timings into narration based on these numbers.
- **Using `properties` as a junk drawer.** Keep keys conventional: `color`, `stroke_width`, `font_size`, `domain`, `x_range`, `y_range`. Bespoke keys silently get ignored by the Manim codegen.
- **Populating `camera` in Phase 1.** It will be dropped on the floor; worse, it creates the illusion that camera direction is wired up when it isn't.
- **Cross-scene element references.** Not a thing in Phase 1. If a concept needs to persist across scenes, the visual planner should re-emit the element.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. Covers the schema as defined in `docs/ARCHITECTURE.md` §5.5. Next revision will land when `schemas/src/pedagogica_schemas/scene_spec.py` is written (Week 2) and field names are confirmed.
