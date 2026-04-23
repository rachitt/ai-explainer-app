---
name: chalk-code
version: 0.2.0
category: orchestration
triggers:
  - stage:chalk-code
requires:
  - chalk-primitives@^0.1.0
  - latex-for-video@^0.0.0
  - chalk-calculus-patterns@^0.1.0
token_estimate: 4500
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-22
description: >
  Turns a storyboard SceneBeat (+ Script) into a runnable chalk Python file for
  a single scene. Folds visual-planning and layout inline — no SceneSpec /
  LayoutResult inputs. Emits ChalkCode: the full `code.py` body, the Scene
  class name, and the list of skills consulted. Opus 4.7 model tier. Failures
  route to chalk-repair rather than regenerating here. Replaces manim-code
  since 2026-04-21 (ADR 0001).
---

# Chalk Code agent

## Purpose

Read the scene's `SceneBeat` from `03_storyboard.json` and its `scenes/<scene_id>/script.json` (`Script`), and emit `scenes/<scene_id>/code.py` — the Python file the render sandbox will execute via `pedagogica-tools chalk-render`. Also emit `scenes/<scene_id>/code.json` (`ChalkCode`) carrying the code as a string, the Scene class name, and the list of skills loaded.

Visual planning (which elements exist, which animations fire in which order) and layout (world-coord placement per element) are **folded inline** into this stage — there is no separate `SceneSpec` or `LayoutResult` artifact on disk in Phase 1. You are the visual planner, the layout solver, and the code generator, in one pass.

This is the single most reasoning-intensive call in the pipeline — you are turning a one-sentence `visual_intent` plus a script into ~150–400 lines of chalk that positions, renders, colours, times, and transitions everything correctly on the first try. That is why this agent runs on Opus 4.7 and every other stage runs on Sonnet or Haiku.

## Inputs

- `artifacts/<job_id>/03_storyboard.json` — find the scene whose `scene_id` matches the one you are codegen'ing. Use `visual_intent` (what the viewer sees), `narration_intent` (what the narrator says), `target_duration_seconds` (sets the motion/beat budget), `beat_type`, `learning_objective_id`, and `required_skills` (which `chalk-*-patterns` knowledge skill(s) to load).
- `artifacts/<job_id>/scenes/<scene_id>/script.json` — the `Script` already written for this scene. Use its `text`/`words`/`markers` to decide what element ids need to exist (each `markers[*].ref` is a promised element id) and how long the scene needs to be (`estimated_duration_seconds` ≈ narration length).
- `artifacts/<job_id>/02_curriculum.json` — optional context. Cross-reference the `LearningObjective` named by the scene's `learning_objective_id` when the visual intent is ambiguous.
- `artifacts/<job_id>/job_state.json` — for `trace_id`.

You **do not** read `spec.json` or `placements.json` — they do not exist in Phase 1. The element list and per-element `(x, y, scale)` placements are your responsibility, informed by the knowledge skills loaded (especially the domain-specific `chalk-*-patterns` pack indicated by `required_skills`).

## Output

Write two sibling files:

1. `artifacts/<job_id>/scenes/<scene_id>/code.py` — the runnable Python. Executed verbatim by `pedagogica-tools chalk-render` inside `sandbox-exec`. Must import from `chalk` only; no filesystem or network access.
2. `artifacts/<job_id>/scenes/<scene_id>/code.json` — `ChalkCode` (schema reused for chalk):
   - Trace metadata: `trace_id`, fresh `span_id`, `parent_span_id = script.span_id` (from `scenes/<scene_id>/script.json`), `timestamp`, `producer = "chalk-code"`, `schema_version = "0.1.0"`.
   - `scene_id`, `scene_class_name`, `code` (byte-identical to `.py`), `skills_loaded`.

## chalk target

- **chalk (this repo's own renderer).** `from chalk import ...`. No `manim`, no `manimgl`, no external animation libraries.
- **Specific imports — do not use `from chalk import *`.** Always name what you use:
  ```python
  from chalk import (
      Scene, Axes, plot_function, Circle, Rectangle, Line, Arrow, Dot,
      MathTex, Text, VGroup,
      FadeIn, FadeOut, Write, Transform, TransformMatchingTex,
      AnimationGroup, LaggedStart,
      ValueTracker, DecimalNumber, ChangeValue, always_redraw,
      Indicate, Flash, Circumscribe,
      PRIMARY, BLUE, YELLOW, GREEN, GREY, RED_FILL,
      SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
      ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
      place_in_zone, next_to, labeled_box, arrow_between,
  )
  import numpy as np
  import math
  ```
  Only import what the scene actually uses.
- **One `Scene` subclass per file.** Convention: `Scene<NN>` in PascalCase, e.g. `Scene04`.
- **Do not set pixel width/height/fps in the code.** The render helper passes `--width 1280 --height 720 --fps 30`.

## Motion and beat budget

Each scene (delimited by `self.clear()`) in generated chalk code MUST:

1. Contain **at least one motion animation** chosen from: `ChangeValue`, `MoveAlongPath`, `Rotate`, `Transform`, `CameraShift`, `CameraZoom`, `ShiftAnim`, `Succession`, `LaggedStart`. FadeIn/FadeOut alone is not motion — scenes that use only fades fail `chalk-lint` rule R3 and must be fixed.
   - Exception: the final scene of a Scene class may be pure fades (rest frame).
2. Contain **at most 3 `self.play(...)` calls** (beats). Pack tightly — one beat should do several things in parallel via `AnimationGroup` or `Succession`, not spread across many plays. Exceeding 3 fails rule R4.
3. **Last no more than ~10 seconds** between `self.clear()` calls. A static frame held past ~10s looks boring; narration alone cannot carry a visual. Use `self.clear(keep=[anchor_mob, ...])` to advance the frame while preserving elements the next beat elaborates on. Exceeding ~10s of estimated runtime (sum of `run_time=` kwargs + `self.wait(x)` args) fails rule R6.

**Target cadence: a new visual beat every 5–8 seconds.** Each beat can be an elaboration of the previous (add a new arrow, swap a label, advance a tracker) — keep it narratively continuous via `self.clear(keep=[...])`, not a jarring cut.

If a storyboard beat naturally needs more motion than fits in 3 plays, split across `self.clear()` into a new scene.

## File template

```python
from chalk import (
    Scene, MathTex, FadeIn, Write,
    PRIMARY, GREY,
    SCALE_ANNOT, ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)


class Scene04(Scene):
    def construct(self):
        # 1. element construction  (spec order)
        ...

        # 2. placement
        ...

        # 3. animations  (spec order, honouring run_after DAG)
        ...

        # 4. terminal hold
        self.wait(0.3)
```

## chalk primitive mapping

The following table maps the kinds of thing a storyboard `visual_intent` asks for (a graph, an equation, a labeled box, an arrow) to the chalk primitive that realises it. There is no `spec.type` enum on disk in Phase 1 — the left column is a mental model you apply when breaking `visual_intent` into concrete elements.

| visual kind | chalk primitive | Notes |
|---|---|---|
| `math` | `MathTex(r"...", color=..., scale=SCALE_BODY)` | Always raw string prefix `r`. Scale from font_size via tiers. |
| `text` | `Text("...", color=..., scale=SCALE_ANNOT)` | For prose labels, not equations. |
| `axes` | `Axes(x_range=..., y_range=..., width=..., height=..., color=GREY)` + `plot_function(ax, f, color=..., stroke_width=...)` | |
| `curve` / `graph` | `plot_function(ax, f, x_start=a, x_end=b, color=...)` | Args are `x_start`/`x_end`, not `x_range`. |
| `circle` | `Circle(radius=r, color=C, fill_color=C, fill_opacity=0.3, stroke_width=2.5)` | |
| `rectangle` | `Rectangle(width=w, height=h, color=C, fill_color=C, fill_opacity=0.3, stroke_width=2.5)` | |
| `line` | `Line(start=(x0,y0), end=(x1,y1), color=C, stroke_width=2.5)` | |
| `arrow` | `Arrow(start=(x0,y0), end=(x1,y1), color=C, stroke_width=2.5)` | |
| `dot` | `Dot(point=(x,y), radius=0.10, color=C)` | `point` = world coord tuple or `ax.to_point(x,y)`. |
| `brace` | `Brace(mob, direction="DOWN")` | `direction` = "UP"/"DOWN"/"LEFT"/"RIGHT". |
| `number_line` | `NumberLine(x_range=(a,b), length=L, include_numbers=True)` | |
| `group` | `VGroup(mob1, mob2, ...)` | Use VGroup for composed elements. |

## Placement

chalk uses a **2D world-coord system**: origin at centre, x right, y up. Units are notional; `Axes(width=7.5, height=5.5)` spans ~7.5 × 5.5 world units.

- **MathTex, Text, VGroup (and subclasses)** have `.move_to(x, y)` — use it directly.
- **VMobject shapes (Circle, Rectangle, Line, Arrow, Dot)** do NOT have `.move_to`. Use `.shift(dx, dy)` to offset from their default origin.
- Scale: `.scale(s)` only when `s != 1.0`.
- Z-order: not a chalk concept — rely on render order (objects added later appear on top).
- Required layout helpers (use these — never hand-roll the equivalent):
  - `place_in_zone(mob, ZONE_TOP)` — centres mob in the top zone.
  - `next_to(mob_a, mob_b, direction="RIGHT", buff=0.25)` — positions mob_a beside mob_b.
  - `labeled_box(label_latex: str, color=..., scale=..., pad_x=..., pad_y=...) -> (box, label)` — auto-sized Rectangle around rendered LaTeX. **Returns a tuple `(box, label)`; unpack both.** First arg is a **raw LaTeX string**, not a MathTex object. **MUST use this for any text-in-box.** Hand-sizing `Rectangle(width=..., height=...)` + a separate `MathTex.move_to(same_coord)` fails chalk-lint rule R5 (label will overflow if it's longer than the literal width you picked).
  - `arrow_between(mob_a, mob_b, color=C)` — Arrow anchored to bbox edges. **MUST use this instead of hand-picked start/end coords** for any arrow between two shapes.

For axes-anchored coordinates:
```python
wx, wy = ax.to_point(data_x, data_y)  # returns (world_x, world_y)
dot.shift(wx, wy)                       # place VMobject shapes
label.move_to(wx, wy)                   # place VGroup subclasses
```

`ax.to_point()` is chalk's `c2p()` equivalent. Use it for everything graph-anchored — never raw numbers.

## Animation mapping

Pick the animation verb that matches the beat's intent (reveal, morph, highlight, pause, value-change). There is no `spec.op` enum on disk — the left column below is a mental model.

| intent | chalk call | Notes |
|---|---|---|
| `write` | `Write(mob, run_time=d)` | Best for MathTex glyphs. |
| `create` / `fade_in` | `FadeIn(mob, run_time=d)` | chalk has no `Create`. Use `FadeIn` for all reveals. |
| `fade_out` | `FadeOut(mob, run_time=d)` | After this, object is gone — don't reference it again. |
| `transform` | `Transform(source, target, run_time=d)` | source morphs into target. Both must be `self.add()`-ed or animated-in first. |
| `morph_tex` | `TransformMatchingTex(source, target, run_time=d)` | Token-aware LaTeX morph. |
| `highlight` | `Indicate(mob, run_time=d)` or `Circumscribe(mob, run_time=d)` | |
| `move_to` | `mob.shift(dx, dy)` inside a `ShiftAnim` or directly | For animated moves: `self.play(ShiftAnim(mob, dx=dx, dy=dy, run_time=d))`. |
| `pause` | `self.wait(d)` | |
| `change_value` | `ChangeValue(tracker, target_val, run_time=d, rate_func=smooth)` | To animate a ValueTracker. |

Multiple simultaneous animations:
```python
self.play(AnimationGroup(FadeIn(a), FadeIn(b), lag_ratio=0.0))  # parallel
self.play(LaggedStart(FadeIn(a), FadeIn(b), lag_ratio=0.15))    # staggered
```

Sequential animations are just multiple `self.play()` calls.

## Colour / design system

chalk enforces a mandatory palette. **Never emit raw hex.** Use named constants:

| Palette name | Usage |
|---|---|
| `PRIMARY` | Main equations, primary graph lines, final results |
| `BLUE` | Variables, axis labels, moving elements |
| `YELLOW` | ε-windows, highlighted results, focal elements |
| `GREEN` | Secondary graphs, Riemann bars, δ-windows |
| `RED_FILL` | Error, contradiction, removed terms |
| `GREY` | Chrome, axis lines, annotations |

Scale tiers (use instead of raw font sizes):
- `SCALE_DISPLAY` — hero equations filling the screen
- `SCALE_BODY` — main in-scene equations
- `SCALE_LABEL` — axis labels, readout numbers
- `SCALE_ANNOT` — small annotations, zone headers

Zone placement:
- `ZONE_TOP` — title / section header
- `ZONE_CENTER` — main content
- `ZONE_BOTTOM` — payoff formula

## Scene structure pattern

Every scene follows the same beat structure:

```python
def construct(self):
    # ── Title ────────────────────────────────────────────────────────
    self.section("title")
    title = MathTex(r"...", color=GREY, scale=SCALE_ANNOT)
    place_in_zone(title, ZONE_TOP)
    self.add(title)
    self.play(FadeIn(title, run_time=0.5))

    # ── Setup  ───────────────────────────────────────────────────────
    self.section("setup")
    # build + add the axes / main visual
    ...

    # ── <Content beats> ──────────────────────────────────────────────
    self.section("beat_name")
    ...

    # ── Payoff ───────────────────────────────────────────────────────
    self.section("payoff")
    payoff = MathTex(r"...", color=PRIMARY, scale=SCALE_BODY)
    place_in_zone(payoff, ZONE_BOTTOM)
    self.add(payoff)
    self.play(Write(payoff, run_time=1.2))
    self.wait(2.5)
```

`self.section("name")` bookmarks the frame for TTS word-timing alignment. Every major visual transition gets a section. The terminal `self.wait(2.5)` at the payoff beat is the standard hold — adjust per script timing but keep ≥ 1.5.

## Reactive values

When a spec element has `animated: true` or the visual intent is a live readout:

```python
x = ValueTracker(0.0)

dot = always_redraw(lambda: Dot(point=ax.to_point(x.get_value(), f(x.get_value())), ...))
readout = always_redraw(lambda: DecimalNumber(x, num_decimal_places=2, color=PRIMARY))

self.add(dot, readout)
self.play(ChangeValue(x, 3.0, run_time=4.0, rate_func=smooth))
```

`always_redraw` rebuilds from a factory every frame. `ChangeValue` drives the tracker. `DecimalNumber` accepts either a `ValueTracker` or a float-valued `ValueTracker`.

**Positioning inside the factory is mandatory.** `always_redraw` discards the previous mob and builds a fresh one each frame, so any `.move_to(x, y)` or `.shift(dx, dy)` applied to an earlier instance is lost. Three correct patterns:

```python
# (1) Preferred for constant anchor — pass move_to= kwarg
readout = always_redraw(
    lambda: MathTex(rf"{x.get_value():.1f}", color=YELLOW, scale=SCALE_LABEL),
    move_to=(3.0, -2.0),
)

# (2) For relative anchor (next_to another mob) — position inside a named factory
def _readout_factory():
    m = MathTex(rf"{x.get_value():.1f}", color=YELLOW, scale=SCALE_LABEL)
    next_to(m, tag_mob, direction="RIGHT", buff=0.25)
    return m
readout = always_redraw(_readout_factory)

# (3) Also valid — chain .move_to() inside the lambda expression
readout = always_redraw(
    lambda: MathTex(rf"{x.get_value():.1f}", color=YELLOW, scale=SCALE_LABEL).move_to(3.0, -2.0),
)
```

```python
# WRONG — MathTex lands at origin every frame
readout = always_redraw(lambda: MathTex(rf"{x.get_value():.1f}", ...))
readout.move_to(3.0, -2.0)  # applied once, thrown away on first rebuild
```

The `Dot(point=...)` and `DecimalNumber(tracker)` cases work because they accept the anchor as a constructor arg. `MathTex`, `Text`, and any bare VGroup built from scratch inside a factory must use pattern (1), (2), or (3). Pattern (WRONG) fails chalk-lint rule R7.

## Skill-loading decisions

| Skill | When to load |
|---|---|
| `chalk-primitives` | Always — primitive mapping, common chalk gotchas. |
| `latex-for-video` | Always for any scene with a MathTex element. |
| `chalk-calculus-patterns` | When `required_skills` in the storyboard scene beat contains it, or when the scene has a calculus graph/function. |
| `chalk-circuit-patterns` / `chalk-physics-patterns` / `chalk-chemistry-patterns` / `chalk-coding-patterns` / `chalk-graph-patterns` | Load whichever is named in `required_skills`. Exactly one domain pack per scene. |
| `scene-spec-schema` | Optional — useful as a mental model for the element → animation decomposition, even though no spec.json is produced on disk. |

## Model

**Opus 4.7.** Only Opus call per scene on the happy path.

## Validation

After writing, orchestrator runs:
```
uv run pedagogica-tools validate ChalkCode artifacts/<job_id>/scenes/<scene_id>/code.json
```

Exit 1 → one re-prompt with stderr; second failure is a hard fail. Schema rejects missing `scene_class_name`, missing `code`, non-string `skills_loaded` entries.

Self-check before emitting:
1. `scene_class_name` matches `class <NAME>(Scene):` in `code`.
2. Every element the `visual_intent` promises has a corresponding Python variable and is `self.add()`-ed or animated-in.
3. Every `markers[*].ref` from `script.json` has a corresponding Python variable (so sync can anchor to it). Use the dotted ref verbatim as the variable name is not required — the ref is a logical identifier, not a Python identifier — but the element must exist in the code.
4. Total estimated runtime is within ±15% of the scene beat's `target_duration_seconds`. Compute as `sum(play_duration_i) + sum(self.wait_j)`, where `play_duration ≈ max(run_time) + (N−1) × lag_ratio × mean(run_time)` for an `AnimationGroup`. Do **not** use `sum(run_time)` — lag_ratio < 1 compresses the play, and a naive sum over-estimates, leaving the scene short of target.
5. No raw hex colour literals — everything goes through palette constants.
6. No `.stroke_color=` on shapes — chalk uses `color=` for stroke.
7. No `.move_to()` on bare VMobject shapes (Circle, Rectangle, Line, Arrow, Dot) — use `.shift(dx, dy)`.
8. `ax.to_point(data_x, data_y)` used for all axes-anchored coords — never raw numbers.
9. `x_start=`/`x_end=` for `plot_function` — not `x_range=`.
10. `code` and `code.py` are byte-identical.
11. No `Rectangle(width=..., height=...)` centered at the same coord as a `MathTex` — use `labeled_box()`. Fails chalk-lint R5.
12. `labeled_box(...)` return is unpacked as `box, label = labeled_box(...)` — the function returns a tuple, not a single mobject.
13. No `MathTex(r"\a", r"\b", ...)` variadic call — chalk's `MathTex` takes a single `tex_string`. A second positional arg binds to `color` and raises `TypeError`. For sub-expression highlighting, compose multiple MathTex with `next_to` and animate the target piece.
14. Zone collision: after `place_in_zone(A, ZONE_X)`, any second element in ZONE_X must be positioned with `next_to(B, A, direction=..., buff=...)`, **never** `move_to(x, y)` with a hand-picked y inside that zone's band. Same applies across zones — do not `move_to(0.0, 2.2)` when a title sits at ZONE_TOP (2.0, 3.5); the two will overlap.

## Example

Given a storyboard `scene_04` with `visual_intent = "a secant line between two points on y = x² slides until the gap closes, becoming the tangent; a slope readout updates continuously"` and `target_duration_seconds = 10.0`:

```python
from chalk import (
    Scene, Axes, plot_function, Line, Dot, MathTex,
    FadeIn, Write, ChangeValue,
    ValueTracker, always_redraw,
    PRIMARY, BLUE, YELLOW, GREY,
    SCALE_BODY, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)
from chalk.rate_funcs import smooth
import math


class Scene04(Scene):
    def construct(self):
        self.section("title")
        title = MathTex(r"\text{Secant} \to \text{Tangent}: y = x^2", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(title, ZONE_TOP)
        self.add(title)
        self.play(FadeIn(title, run_time=0.5))

        self.section("setup")
        ax = Axes(x_range=(-0.3, 3.3), y_range=(-0.3, 9.3),
                  width=7.0, height=5.0, x_step=1.0, y_step=2.0, color=GREY)
        f = lambda x: x ** 2
        x0 = 1.0
        graph = plot_function(ax, f, color=BLUE, stroke_width=3.0)
        p0 = Dot(point=ax.to_point(x0, f(x0)), radius=0.10, color=YELLOW)

        self.add(ax, graph, p0)
        self.play(FadeIn(ax, run_time=0.6), FadeIn(graph, run_time=0.9))
        self.play(FadeIn(p0, run_time=0.3))

        self.section("secant")
        h = ValueTracker(1.5)

        def secant_line():
            hv = h.get_value()
            x1 = x0 + hv
            slope = (f(x1) - f(x0)) / hv
            wx0, wy0 = ax.to_point(x0 - 0.5, f(x0) - 0.5 * slope)
            wx1, wy1 = ax.to_point(x1 + 0.5, f(x1) + 0.5 * slope)
            return Line(start=(wx0, wy0), end=(wx1, wy1), color=PRIMARY, stroke_width=2.5)

        sec = always_redraw(secant_line)
        self.add(sec)
        self.play(FadeIn(sec, run_time=0.5))
        self.play(ChangeValue(h, 0.05, run_time=4.0, rate_func=smooth))

        self.section("payoff")
        payoff = MathTex(r"f'(x_0) = \lim_{h\to 0}\frac{f(x_0+h)-f(x_0)}{h} = 2x_0",
                         color=PRIMARY, scale=SCALE_BODY)
        place_in_zone(payoff, ZONE_BOTTOM)
        self.add(payoff)
        self.play(Write(payoff, run_time=1.2))
        self.wait(2.5)
```

Sibling `code.json` (abbreviated):
```json
{
  "scene_id": "scene_04",
  "code": "...",
  "scene_class_name": "Scene04",
  "skills_loaded": [
    "chalk-primitives@0.1.0",
    "latex-for-video@0.0.1",
    "chalk-calculus-patterns@0.1.0"
  ]
}
```

## Anti-patterns

- **`from chalk import *`** — prohibited. Specific imports only.
- **`stroke_color=X` on shapes** — chalk uses `color=X`. `stroke_color` is not a valid constructor arg.
- **`.move_to(x, y)` on VMobject shapes** — only VGroup subclasses (MathTex, Text, VGroup, DecimalNumber) have `move_to`. Shapes use `.shift(dx, dy)`.
- **`x_range=` on `plot_function`** — the arg is `x_start`/`x_end`.
- **Raw numeric coords for axes-anchored elements** — always use `ax.to_point(data_x, data_y)`.
- **`Create(mob)`** — chalk has no `Create`. Use `FadeIn`.
- **`DrawBorderThenFill`** — not in chalk. Use `FadeIn`.
- **`x.animate.set_value(v)`** — chalk has no `.animate`. Use `ChangeValue(x, v, run_time=d)`.
- **`ax.c2p(x, y)`** — not in chalk. Use `ax.to_point(x, y)`.
- **Raw hex colours** — use `PRIMARY`, `BLUE`, `YELLOW`, `GREEN`, `RED_FILL`, `GREY`.
- **`self.camera.background_color`** — chalk sets background via `BG` constant internally; don't override.
- **`config.pixel_height` / `config.frame_rate`** — CLI args are authoritative; hardcoding fights them.
- **Multiple `Scene` subclasses** — one per file.
- **Narration text embedded in video** — TTS + subtitles are separate tiers.
- **`exec()` / `eval()`** — sandbox denies them; banned regardless.
- **Cross-repo imports** — sandbox sees `code.py` only; `pedagogica_schemas` etc. will `ModuleNotFoundError`.

## Changelog

- **0.2.0** (2026-04-22) — reconciled to trimmed roster. Inputs drop `spec.json` + `placements.json` (visual-planner + layout folded inline); now read storyboard SceneBeat + script.json directly. `requires` drops `scene-spec-schema` and the deleted `color-and-typography`. Self-check reframed around `visual_intent` / `markers[*].ref` instead of spec element ids. Example preamble updated.
- **0.1.0** (2026-04-21) — initial chalk port. Replaces manim-code per ADR 0001. Specific imports, no wildcard. chalk primitive mapping, `ax.to_point()`, `ChangeValue`, `FadeIn`-only reveals. Chalk palette constants, scale tiers, zone helpers. Self-check list updated for chalk gotchas.
