---
name: scene-composition
version: 0.1.0
category: manim
triggers:
  - stage:storyboard
  - stage:visual-planner
  - stage:layout
  - stage:manim-code
requires:
  - scene-spec-schema@^0.1.0
  - color-and-typography@^0.1.0
  - pedagogy-cognitive-load@^0.1.0
token_estimate: 2600
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Layout, framing, reading order, and split-screen rules for a 720p Manim scene.
  Frame zoning, safe areas, anchor points, element spacing, where math goes vs
  where labels go, how to read the scene left-to-right or top-to-bottom, and
  when to split the frame into two panels. Used by the storyboard agent to
  choose framings per beat, by the visual planner to place elements, by the
  layout agent to assign concrete positions, and consulted by the Manim code
  agent for default placements when the layout pass leaves them unset.
---

# scene-composition

## Purpose

`pedagogy-cognitive-load` caps *how much* can be on screen; `color-and-typography` says *which colours*. This skill is the spatial half: *where* each element goes, what reads first, what sits next to what. A well-composed scene lets the viewer's eye find the payload without instruction; a badly composed one forces the narration to do work the visual should have done.

Phase 1 uses a single frame geometry (Manim default 14×8 units at 720p), a fixed set of zones, and three framings (single-focus, side-by-side, text-plus-visual). The skill's job is to make those choices and their tradeoffs explicit so the visual planner doesn't reinvent them per scene.

## When to load

- Storyboard agent — **always**. Framing is a storyboard-level decision that feeds `SceneBeat` intent.
- Visual planner — **always**. Every element placement is a composition decision.
- Layout agent — **always**. Turns the planner's intent into concrete coordinates with overlap checks.
- Manim code agent — **conditional**. If `LayoutResult.placements` is complete, the code agent doesn't need this skill. If any element was left unplaced (explicit opt-in via `properties.auto_place: true`), load this to pick defaults.
- Script, TTS, sync — not needed.

## Core content

### 1. Frame geometry

Manim's default scene is **14 units wide × 8 units tall**, origin at centre. At 720p that's 1280 × 720 px; one Manim unit ≈ 91 px horizontally, 90 px vertically.

```
                    +4 (top edge)
                     |
   -7 ─────── 0 ─────── +7   (x axis, 14 units wide)
                     |
                    -4 (bottom edge)
```

### 2. Safe area

Never place readable content closer than **0.5 units** from any edge. At 720p, ≈ 45 px margin. Safe area is therefore `x ∈ [-6.5, +6.5]`, `y ∈ [-3.5, +3.5]`.

Why: YouTube and embedded players occasionally overlay captions, progress scrubbers, or controls across the bottom ~8% and top ~6%. A 0.5-unit margin keeps the scene legible under all common overlay conditions.

Axes, grid lines, and other decorative content *may* extend to the edge; labelled or animated content may not.

### 3. The six zones

Every scene divides the safe area into six zones. The visual planner picks one zone per element.

```
┌───────────────────────────────┐
│ TL          TOP             TR│    y ∈ [+2.0, +3.5]
│                               │
│ LEFT       CENTER        RIGHT│    y ∈ [-2.0, +2.0]   ← main visual real estate
│                               │
│ BL        BOTTOM            BR│    y ∈ [-3.5, -2.0]
└───────────────────────────────┘
```

Zone use (semantic, not a hard grid):

| Zone | Role | Typical contents |
|---|---|---|
| **CENTER** | The thing you're looking at | The anchor example: graph, main equation, primary diagram. |
| **TOP** | Beat title / current concept name | The formal name being introduced, e.g. `\frac{df}{dx}`. Appears after "name after show". |
| **BOTTOM** | Running caption or worked step | Current computational step, e.g. `f'(1) = 2`. Only when the step is worth keeping. |
| **LEFT / RIGHT** | Secondary content in a side-by-side framing | See §5. In single-focus framings, keep empty. |
| **TL / TR / BL / BR** | Annotations, legend, micro-callouts | Small; never the payload. |

A single scene uses **at most 3 zones** active at any rest frame. Empty zones are not wasted — they're breathing room.

### 4. Reading order

Western reading: top-down, left-right. The composition must support one of two reading orders per scene, chosen at the storyboard:

- **Vertical**: eye starts at TOP (orienting label), moves to CENTER (main visual), ends at BOTTOM (running step or payoff). Best for define / generalize beats where the concept is named first, shown, then expressed.
- **Horizontal**: eye starts at LEFT, moves to RIGHT. Best for compare/contrast beats (§5).

The *first* element that animates in sets the entry point of the reading order. If the first animation is `anim.write.eq_top`, the scene reads vertical; if it's `anim.create.panel_left`, horizontal.

**Rule**: don't mix reading orders inside one scene. A scene that introduces a TOP label, then pulls attention LEFT, then drops it BOTTOM is a scene the eye can't follow in real time.

### 5. Three framings

All Phase 1 scenes are one of these three.

#### 5.1 Single-focus (default)

One object dominates CENTER; optional TOP label and optional BOTTOM step. LEFT/RIGHT empty.

Use for: hook, define, motivate, generalize, most example beats.

Placement defaults:

- Main visual centred at `(0, 0)`, scaled so its bounding box fits in `x ∈ [-5, +5]`, `y ∈ [-2, +2]`.
- TOP label at `(0, +2.8)`, `font_size=48`.
- BOTTOM step at `(0, -2.8)`, `font_size=36`.

#### 5.2 Side-by-side (compare/contrast)

Two panels, split at `x = 0`. LEFT panel in `x ∈ [-6.5, -0.5]`, RIGHT in `x ∈ [+0.5, +6.5]`. A narrow vertical separator (a thin line at `x=0`) is optional but helps the eye commit to one side at a time.

Use for: compare/contrast pattern (see `explanation-patterns`), e.g. average vs instantaneous rate, before/after of a transformation.

Placement defaults:

- Each panel's content centred on its half: LEFT at `(-3.5, 0)`, RIGHT at `(+3.5, 0)`.
- Panel labels at the top of their half: LEFT-label at `(-3.5, +2.8)`, RIGHT-label at `(+3.5, +2.8)`.
- Each panel's content scaled to fit in a 5×4 bounding box.
- TOP/BOTTOM zones reserved for shared content that applies to both panels (e.g. the diff callout).

#### 5.3 Text-plus-visual (derivation)

LEFT panel holds a growing piece of text or a LaTeX derivation; RIGHT panel holds the corresponding visual. New lines of text animate onto LEFT; the visual on RIGHT updates in sync.

Use for: first-principles build-up, FTC-style derivations, algebraic manipulations with visual confirmation.

Placement defaults:

- LEFT: text top-anchored at `(-3.5, +3.0)`, grows downward; `font_size=36` for display math, `28` for text.
- RIGHT: visual centred at `(+3.5, 0)`, same 5×4 bounding box as §5.2.
- A light guide separator at `x = 0` is optional.

### 6. Element spacing

Minimum gaps between adjacent readable elements, in Manim units:

| Between | Minimum gap |
|---|---|
| Two labels | 0.3 (≈27 px) |
| Label and its object (arrow, curve) | 0.15 (≈14 px) — labels may sit close to what they label |
| Two equations at display size | 0.6 (≈54 px vertical) |
| Panel contents to panel edge (side-by-side) | 0.4 |
| Anything to the frame safe-area edge | 0.5 |

The layout agent's `overlap_warnings` list flags violations. In Phase 1, violations block the render.

### 7. Anchors and co-moving groups

Elements that belong together move together. The layout agent groups them via a shared `z_order` and the Manim code agent emits them as a Manim `VGroup`. Canonical groups:

- **Graph + its axes** — always grouped. Rescaling the axes must rescale the graph.
- **Equation + its annotation underbrace** — grouped. Move as a unit.
- **Point + its coordinate label** — grouped. The label follows the point.
- **Panel contents** (side-by-side) — each panel is a group; the panel can be animated as one unit.

A scene with three semantic groups is usual; four is the ceiling.

### 8. Framing choice from `SceneBeat`

The storyboard sets `beat_type`. Default framing per beat type:

| `beat_type` | Default framing | Notes |
|---|---|---|
| `hook` | Single-focus | The hook has one image; anything else dilutes it. |
| `define` | Single-focus | Name goes TOP, instance CENTER. |
| `motivate` | Single-focus, or side-by-side | Side-by-side when motivating *against* a neighbour. |
| `example` | Single-focus; text-plus-visual for multi-step | Derivation beats earn the LEFT column. |
| `generalize` | Single-focus | The general form occupies CENTER; specifics fade. |
| `recap` | Single-focus, return to anchor | Recap is not the place for a new framing. |

Overrides are allowed but require a one-line justification in `SceneBeat.visual_intent`.

### 9. Density at rest vs during animation

A scene in motion tolerates more on screen than a scene at rest. Budget:

- **Rest frame**: ≤ 5 salient pieces (echoes `pedagogy-cognitive-load` rest-frame rule).
- **During animation**: the incoming element doesn't count against the rest-frame cap while it's still animating. This is why a scene can "introduce" a new label without dropping an old one, provided the old one fades before the next rest frame.

The layout agent should set `z_order` so animating elements are drawn above stationary ones; otherwise the viewer sees a stale rest frame for a frame or two.

## Examples

### Example 1 — single-focus derivative beat

See `examples/example_01_single_focus_placements.json`: parabola centred, axes grouped with it, TOP label `f(x) = x^2`, BOTTOM running step `f'(1) = 2`. Vertical reading order. Four elements, three zones.

### Example 2 — side-by-side (average vs instantaneous rate)

See `examples/example_02_side_by_side_placements.json`: LEFT panel shows the secant between two fixed points with the rise/run callout; RIGHT panel shows the same parabola with the moving tangent and its slope number. Horizontal reading order. Shared TOP zone holds the question "What's the difference?".

### Example 3 — text-plus-visual (Riemann sum → integral)

See `examples/example_03_text_plus_visual.py`: LEFT builds up a line at a time (`∑ f(x_i) Δx` → `lim_{n→∞} ∑…` → `∫_a^b f(x) dx`); RIGHT shows the rectangles shrinking until they become the smooth area. Each new line on LEFT anchors to a word in the narration; each shrink step on RIGHT anchors to the same words. Layout agent outputs a matching `LayoutResult` (see `examples/example_03_expected_layout.json`).

### Counter-example — zone salad

A scene that places the main equation in TR, the graph LEFT, a running step at BL, a caption at BOTTOM, and a highlight arrow floating in TL. Five zones active; no reading order; viewer's eye ricochets. Fix: collapse to single-focus (graph CENTER, running step BOTTOM, nothing else).

## Gotchas / anti-patterns

- **Using CENTER as a dumping ground.** CENTER is for the anchor. A label and the graph it describes can both live in CENTER only if they're a grouped VGroup that reads as one object.
- **Framing mismatch with beat shape.** Compare/contrast pattern in a single-focus framing produces a scene where both halves fight for CENTER; DMEG in side-by-side produces empty panels. Pick the framing with the pattern.
- **Edge-bleeding labels.** Text at `y = +3.7` looks fine in the editor and disappears under YouTube captions. Honour the safe area.
- **Stale rest frames.** Element fades should finish before the next animation's start; otherwise a rest frame includes a half-faded old element. Sequence fades explicitly via `run_after`.
- **Too many semantic groups.** Three groups fit; four is tight; five means the layout is wrong.
- **Mid-scene reframing.** Switching from single-focus to side-by-side mid-scene costs 1+ seconds of viewer re-orientation and almost never earns it. Reframe at scene boundaries only.
- **Manual micro-tweaks.** If a placement needs adjusting by < 0.15 units to look right, the layout is fine — the eye won't notice. Don't over-specify coordinates.
- **Letting the layout agent's `overlap_warnings` slide.** In Phase 1 the warnings block the render. Treating them as advisory is the easy path to a scene that crops text under captions.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. Frame geometry, safe area, six zones, three framings, spacing table, grouping rules, framing-from-beat default table. Worked examples for single-focus, side-by-side, and text-plus-visual. Paired with `scene-spec-schema` and `color-and-typography`.
