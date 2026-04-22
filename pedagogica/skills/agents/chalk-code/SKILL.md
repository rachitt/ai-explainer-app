---
name: chalk-code
version: 0.1.0
category: orchestration
triggers:
  - stage:chalk-code
requires:
  - scene-spec-schema@^0.1.0
  - chalk-primitives@^0.1.0
  - latex-for-video@^0.0.0
  - color-and-typography@^0.1.0
  - chalk-calculus-patterns@^0.1.0
token_estimate: 4500
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-21
description: >
  Turns a SceneSpec + LayoutResult (+ optional Script) into a runnable chalk
  Python file for a single scene. Emits ChalkCode — the full `code.py` body,
  the Scene class name, and the list of skills consulted. Opus 4.7 model tier.
  Reserved for first-pass codegen; failures route to chalk-repair rather than
  regenerating here. Replaces manim-code since 2026-04-21 (ADR 0001).
---

# Chalk Code agent

## Purpose

Read `scenes/<scene_id>/spec.json` (`SceneSpec`), `scenes/<scene_id>/placements.json` (`LayoutResult`), and (when present) `scenes/<scene_id>/script.json` (`Script`), and emit `scenes/<scene_id>/code.py` — the Python file the render sandbox will execute via `pedagogica-tools chalk-render`. Also emit `scenes/<scene_id>/code.json` (`ManimCode`) carrying the code as a string, the Scene class name, and the list of skills loaded.

This is the single most reasoning-intensive call in the pipeline — you are turning a semantic graph of elements and animations into ~150–400 lines of chalk that positions, renders, colours, times, and transitions everything correctly on the first try. That is why this agent runs on Opus 4.7 and every other stage runs on Sonnet or Haiku.

## Inputs

- `artifacts/<job_id>/scenes/<scene_id>/spec.json` — the `SceneSpec`. Every `SceneElement` → a chalk object; every `SceneAnimation` → a `self.play(...)` or `self.wait(...)`.
- `artifacts/<job_id>/scenes/<scene_id>/placements.json` — the `LayoutResult`. Every element's `(position, scale, z_order, font_size)` comes from here, not from the spec's `properties`.
- `artifacts/<job_id>/scenes/<scene_id>/script.json` — the `Script`, when available. Use its `markers` to confirm element ids exist.
- `artifacts/<job_id>/03_storyboard.json` — the matching `SceneBeat` for `required_skills` and `visual_intent`.
- `artifacts/<job_id>/job_state.json` — for `trace_id`.

## Output

Write two sibling files:

1. `artifacts/<job_id>/scenes/<scene_id>/code.py` — the runnable Python. Executed verbatim by `pedagogica-tools chalk-render` inside `sandbox-exec`. Must import from `chalk` only; no filesystem or network access.
2. `artifacts/<job_id>/scenes/<scene_id>/code.json` — `ManimCode` (schema reused for chalk):
   - Trace metadata: `trace_id`, fresh `span_id`, `parent_span_id = layout.span_id`, `timestamp`, `producer = "chalk-code"`, `schema_version = "0.1.0"`.
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

| spec `type` | chalk primitive | Notes |
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
  - `labeled_box(label_tex, color=..., scale=..., pad_x=..., pad_y=...)` — auto-sized Rectangle around a MathTex. **MUST use this for any text-in-box.** Hand-sizing `Rectangle(width=..., height=...)` + a separate `MathTex.move_to(same_coord)` fails chalk-lint rule R5 (label will overflow if it's longer than the literal width you picked).
  - `arrow_between(mob_a, mob_b, color=C)` — Arrow anchored to bbox edges. **MUST use this instead of hand-picked start/end coords** for any arrow between two shapes.

For axes-anchored coordinates:
```python
wx, wy = ax.to_point(data_x, data_y)  # returns (world_x, world_y)
dot.shift(wx, wy)                       # place VMobject shapes
label.move_to(wx, wy)                   # place VGroup subclasses
```

`ax.to_point()` is chalk's `c2p()` equivalent. Use it for everything graph-anchored — never raw numbers.

## Animation mapping

| spec `op` | chalk call | Notes |
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

## Skill-loading decisions

| Skill | When to load |
|---|---|
| `scene-spec-schema` | Always. |
| `chalk-primitives` | Always — primitive mapping, common chalk gotchas. |
| `latex-for-video` | Always for any scene with a `math`-typed element. |
| `color-and-typography` | Always — palette table is authoritative. |
| `chalk-calculus-patterns` | When storyboard `required_skills` contains it, or when the scene has a calculus graph/function. |

## Model

**Opus 4.7.** Only Opus call per scene on the happy path.

## Validation

After writing, orchestrator runs:
```
uv run pedagogica-tools validate ManimCode artifacts/<job_id>/scenes/<scene_id>/code.json
```

Exit 1 → one re-prompt with stderr; second failure is a hard fail. Schema rejects missing `scene_class_name`, missing `code`, non-string `skills_loaded` entries.

Self-check before emitting:
1. `scene_class_name` matches `class <NAME>(Scene):` in `code`.
2. Every `element.id` from the spec has a corresponding Python variable and is `self.add()`-ed or animated-in.
3. Every `animation.id` appears as exactly one `self.play()` or `self.wait()`.
4. No raw hex colour literals — everything goes through palette constants.
5. No `.stroke_color=` on shapes — chalk uses `color=` for stroke.
6. No `.move_to()` on bare VMobject shapes (Circle, Rectangle, Line, Arrow, Dot) — use `.shift(dx, dy)`.
7. `ax.to_point(data_x, data_y)` used for all axes-anchored coords — never raw numbers.
8. `x_start=`/`x_end=` for `plot_function` — not `x_range=`.
9. `code` and `code.py` are byte-identical.
10. No `Rectangle(width=..., height=...)` centered at the same coord as a `MathTex` — use `labeled_box()`. Fails chalk-lint R5.

## Example

Given the visual-planner's `scene_04` — secant-to-tangent on `y = x²`:

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
    "scene-spec-schema@0.1.0",
    "chalk-primitives@0.1.0",
    "latex-for-video@0.0.1",
    "color-and-typography@0.1.0",
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

- **0.1.0** (2026-04-21) — initial chalk port. Replaces manim-code per ADR 0001. Specific imports, no wildcard. chalk primitive mapping, `ax.to_point()`, `ChangeValue`, `FadeIn`-only reveals. Chalk palette constants, scale tiers, zone helpers. Self-check list updated for chalk gotchas.
