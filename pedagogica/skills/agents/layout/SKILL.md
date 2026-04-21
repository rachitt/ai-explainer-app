---
name: layout
version: 0.0.1
category: orchestration
triggers:
  - stage:layout
requires:
  - scene-spec-schema@^0.1.0
  - scene-composition@^0.0.0
  - color-and-typography@^0.1.0
token_estimate: 2400
tested_against_model: claude-sonnet-4-6
owner: rachit
last_reviewed: 2026-04-20
description: >
  Places every element of a SceneSpec inside Manim's 14×8 coordinate window:
  positions, scales, z-order, font sizes, and overlap warnings the Manim code
  agent can act on before rendering.
---

# Layout agent

## Purpose

Read `scenes/scene_NN/spec.json` (`SceneSpec`) and emit `scenes/scene_NN/placements.json` (`LayoutResult` — see `schemas/src/pedagogica_schemas/layout.py`). The Manim code agent will apply these placements when emitting Python.

The visual planner says **what** is on screen and **what order** animations fire. This agent says **where** each element lives in Manim coordinates and **how big** it renders.

## Inputs

- `artifacts/<job_id>/scenes/scene_NN/spec.json` — the `SceneSpec` to lay out.
- `artifacts/<job_id>/03_storyboard.json` — for the beat's `beat_type` and `visual_intent`. Useful for framing decisions; not strictly required.

## Output

Write `artifacts/<job_id>/scenes/scene_NN/placements.json`. Fields:

- Trace metadata: `trace_id` copied from the spec, fresh `span_id`, `parent_span_id = spec.span_id`, `timestamp`, `producer = "layout"`, `schema_version = "0.0.1"`.
- `scene_id`: exactly matches the spec.
- `placements`: one `ElementPlacement` per element in the spec — no extras, no omissions.
- `overlap_warnings`: list of human-readable strings. Empty list = clean.
- `frame_bounds_ok`: `true` if every element fits inside the safe area; `false` otherwise.

### `ElementPlacement`

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Must match an element id in the spec exactly. |
| `position` | `[float, float]` | Manim coordinates `(x, y)` of the element's anchor (centre for text / math / shape; origin for graphs / axes). Serialized as a 2-array. |
| `scale` | `float` | Multiplier. `1.0` = no scaling. Use sparingly — prefer `font_size` for text and `x_range`/`y_range` for graphs. |
| `z_order` | `int` | Higher values draw on top. Default tier system below. |
| `font_size` | `float \| null` | For text/math/label elements, the rendered font size (Manim units). `null` for non-text elements. If the spec's `properties.font_size` is set, pass it through unless it violates the legibility floor. |

## Coordinate system and safe area

Manim's default frame is **14 wide × 8 tall**, centred at the origin:

- x ∈ `[-7.0, +7.0]`
- y ∈ `[-4.0, +4.0]`

Reserve a safe-area margin of **0.5 Manim units** on all sides (≈46 px at 720p). Effective placement region:

- x ∈ `[-6.5, +6.5]`
- y ∈ `[-3.5, +3.5]`

`frame_bounds_ok` is `true` only if every element's estimated bounding box (see "Estimated bounds" below) fits inside the **effective** region.

## Default framing slots

Use these as starting positions; adjust for overlap.

| Slot | Position | Use for |
|---|---|---|
| Centre-stage | `(0.0, 0.0)` | The display math / primary figure of the beat |
| Top-banner | `(0.0, 3.0)` | Section title, scene chapter marker |
| Bottom-caption | `(0.0, -3.0)` | Annotation, "so far so good" notes |
| Left-panel | `(-4.0, 0.0)` | A secondary figure paired with the centre |
| Right-panel | `(+4.0, 0.0)` | A secondary figure or a result slot |
| Corners (NW…SE) | `(±5.5, ±3.0)` | Thumbnails, small labels |

Graphs / axes typically anchor at the origin and use their `properties.x_range` / `y_range` to occupy roughly `[-5, 5] × [-3, 3]` in screen coords. Pin labels to their referent with a small offset (`≈ 0.4`–`0.8` units) rather than an absolute position.

## Z-order tiers

Use these defaults; break ties by spec order. Higher = on top.

| Tier | Range | What goes here |
|---|---|---|
| Background | `0` | Reserved; Phase 1 uses a flat background, no elements here. |
| Axes / chrome | `1–4` | `axes`, gridlines, thin reference shapes |
| Primary figures | `5–9` | `graph`, large `shape`, the focus object |
| Text & math | `10–14` | `math`, `text`, `label` |
| Emphasis overlays | `15–19` | `arrow`, `highlight` boxes, annotation strokes that should sit on top |

Text on top of figures is almost always correct. If it isn't, the planner should restructure the spec, not the layout agent invert z-order.

## Font-size pass-through and the legibility floor

- If an element has `properties.font_size` in the spec, copy it to `font_size` in the placement.
- Otherwise fall back to the defaults from `color-and-typography`:
  - Display math → `48`
  - Body math → `36`
  - Labels on objects → `28`
  - Annotations / captions → `22`
- For non-text elements (`axes`, `graph`, `shape`, `arrow`, `image`), set `font_size: null`.
- **Minimum: 20.** Never emit `font_size < 20` for any text/math/label element. If the layout seems to require smaller text, the layout is wrong — drop a redundant element or push it to a later beat.

## Estimated bounds (for overlap and frame checks)

The layout agent does not render; it reasons about bounding boxes approximately. Use these in Manim units:

| Element type | Width | Height |
|---|---|---|
| `math` | `0.55 × char_count × font_size/48` | `1.2 × font_size/48` |
| `text` / `label` | `0.35 × char_count × font_size/28` | `0.8 × font_size/28` |
| `graph` | derived from `x_range`/`y_range` scaled to a `~10 × 6` window | same |
| `axes` | `~10 × 6` by default | same |
| `arrow` | length implied by endpoints; use `3.0` if unknown | `0.2` |
| `shape` | `properties.width` × `properties.height` if given, else `1.0 × 1.0` | |
| `image` | `properties.width` × `properties.height` if given, else `3.0 × 3.0` | |

Two elements **overlap** when their bounding boxes intersect by more than `0.3` Manim units in **both** axes. A small overlap between a label and its reference arrow is fine and expected.

## Overlap warnings

Every pair of elements that overlaps beyond the tolerance gets one line in `overlap_warnings`:

```
"overlap: <id_a> and <id_b> (x_overlap=<dx>, y_overlap=<dy>)"
```

Warnings do **not** fail the layout. They are signal for the Manim code agent (which may nudge a label by a small delta) and for the Phase-2 repair loop (which may re-invoke the planner to re-chunk the scene). Phase 1 ships the scene as planned.

If `frame_bounds_ok` is `false`, include one warning per out-of-bounds element:

```
"out_of_bounds: <id> at (x, y) exceeds safe area (|x|>6.5 or |y|>3.5)"
```

Two elements that share an anchor because of a `transform` (e.g. `arrow.secant` morphing into `arrow.tangent`) are an expected exception — do **not** warn for those. Detect by checking whether any animation has `op: "transform"` with both ids in `target_ids`.

## Planning heuristics

- **Anchor the beat's subject at centre.** The display equation of a `define` beat, the graph of an `example` beat, the question of a `hook` beat.
- **Labels attach to their referent**, not to an absolute slot. `label.slope` belongs near the tangent arrow; compute its position as the arrow midpoint plus an offset, not `(0, 0)`.
- **Parallel elements parallel each other.** Two items in a compare/contrast pattern go to left-panel and right-panel, not centre-stage and corner-NW.
- **Fewer, bigger beats the grid.** A 3-element scene at 48 pt centre-stage reads better than a 6-element scene at 36 pt. When density is high, drop labels or surface a warning rather than silently shrinking text.
- **`highlight` overlays need ~0.5 unit padding** around the highlighted element or the box clips the glyph.

## Model

Sonnet 4.6.

## Validation

After writing the file, the orchestrator will run:

```
uv run pedagogica-tools validate LayoutResult artifacts/<job_id>/scenes/scene_NN/placements.json
```

Non-zero exit is a failure. You will be re-prompted once with the validator's stderr; a second failure is a hard fail. The validator rejects:

- Unknown fields (`extra="forbid"`).
- Non-numeric positions, negative scales.
- Missing required fields on `ElementPlacement`.

The validator does **not** check overlap (that's `overlap_warnings`), frame-bounds accuracy (`frame_bounds_ok` is your assertion, not a derived field), z-order sanity, or one-placement-per-spec-element. Cross-check those manually before emitting:

- Every `id` in `placements` appears as an element `id` in the spec.
- Every spec element has exactly one placement.
- No duplicate placement ids.

## Example

Input — `scenes/scene_04/spec.json` (excerpt from the visual-planner example):

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
    {"id": "anim.transform.sec2tan", "op": "transform", "target_ids": ["arrow.secant", "arrow.tangent"], "duration_seconds": 1.6, "run_after": "anim.fade_in.h"}
  ]
}
```

Output — `scenes/scene_04/placements.json`:

```json
{
  "scene_id": "scene_04",
  "placements": [
    {"id": "axes.main",      "position": [0.0, 0.0], "scale": 1.0, "z_order": 2,  "font_size": null},
    {"id": "graph.parabola", "position": [0.0, 0.0], "scale": 1.0, "z_order": 6,  "font_size": null},
    {"id": "arrow.secant",   "position": [1.0, 1.0], "scale": 1.0, "z_order": 16, "font_size": null},
    {"id": "arrow.tangent",  "position": [1.0, 2.0], "scale": 1.0, "z_order": 17, "font_size": null},
    {"id": "label.h",        "position": [2.2, 1.4], "scale": 1.0, "z_order": 12, "font_size": 28.0}
  ],
  "overlap_warnings": [],
  "frame_bounds_ok": true
}
```

`arrow.secant` and `arrow.tangent` share an anchor because the `transform` morphs one into the other — they're allowed to overlap (the transform-pair exception). `label.h` offsets to the tangent's midpoint so it reads alongside, not through.

## Anti-patterns

- **Re-emitting element properties** (`type`, `content`, `color`). The layout output is placement-only.
- **Positioning outside `[-6.5, 6.5] × [-3.5, 3.5]`** without setting `frame_bounds_ok: false` and adding an `out_of_bounds:` warning.
- **Using `scale` to shrink text** below the 20 pt floor. Use `font_size` explicitly and refuse to cross the floor.
- **Stacking everything at the origin.** The default centre slot is reserved for the beat's subject; everything else earns its position.
- **Silently dropping overlaps.** If two elements overlap, warn. If they genuinely can't coexist, surface that in `overlap_warnings` — don't relocate an unrelated label off-screen to make room.
- **Filling z-order with arbitrary big integers.** Use the tier system; gaps are fine.
- **Absolute label positions.** Labels attach to their referent; absolute slots break when the referent moves between iterations.
- **Warning on a `transform` pair.** Two elements that share an anchor because of a `transform` is the intended shape, not a layout error.

## Changelog

- **0.0.1** (2026-04-20) — initial Phase 1 draft. Manim 14×8 window with 0.5-unit safe margin, 20 pt legibility floor, five-tier z-order system, overlap tolerance 0.3, transform-pair exemption.
