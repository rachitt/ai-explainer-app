---
name: chalk-primitives
version: 0.1.0
category: chalk
triggers:
  - stage:chalk-code
  - stage:chalk-repair
  - scene_type:any
requires:
  - scene-spec-schema@^0.1.0
token_estimate: 5500
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-21
description: >
  The core chalk primitives every pedagogica scene is built from — MathTex,
  Axes/plot_function, ValueTracker/always_redraw/ChangeValue, shapes, layout
  helpers, and the full animation vocabulary — with runnable examples and the
  timing, coordinate, and import conventions the chalk-code agent needs to emit
  working scenes on the first pass. Loaded on every chalk codegen and repair.
  Replaces manim-primitives as of 2026-04-21 per ADR 0001.
---

# chalk-primitives

## Purpose

chalk is pedagogica's visual primitive (see ADR 0001). Every scene is assembled from the classes and helpers in this skill. Mastering them is 90% of the job; the rest is composition. This skill documents them with runnable examples and the conventions that make scenes compile and look correct on the first pass.

Every example in `examples/` is a complete, runnable `Scene` subclass. Render via:

```bash
cd chalk
uv run chalk examples/example_NN_name.py -s ClassName -o /tmp/out.mp4 --width 1280 --height 720
```

If an example fails to render in CI, the skill ships broken.

## When to load

- **chalk-code agent — always.** Every scene uses these primitives.
- **chalk-repair agent — always.** Repair needs the same vocabulary.
- **visual-planner — no.** The planner works in animation verbs (`fade_in`, `transform_to`); classes are an implementation concern.

---

## 1. Imports — the only correct pattern

```python
from chalk import (
    Scene, MathTex, Circle, Rectangle, Line, Arrow,
    Dot, Polygon, RegularPolygon, ArcBetweenPoints,
    Axes, plot_function, NumberLine, NumberPlane,
    VGroup,
    FadeIn, FadeOut, Write, Transform, ShiftAnim,
    ChangeValue, MoveAlongPath, Rotate,
    AnimationGroup, Succession, LaggedStart,
    Indicate, Flash, Circumscribe,
    TransformMatchingTex,
    ValueTracker, always_redraw, DecimalNumber,
    Brace, brace_label,
    PRIMARY, YELLOW, BLUE, GREEN, RED_FILL, GREY, TRACK,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
    place_in_zone, next_to,
)
from chalk.rate_funcs import linear, smooth, there_and_back
```

**Never** import raw hex colors or magic-number scales inside a scene file. All palette constants and scale tiers come from `chalk` (re-exported from `chalk.style`). See `color-and-typography` for semantics.

---

## 2. MathTex — every formula and label

`MathTex(r"...", color=..., scale=...)` renders LaTeX math via pycairo (no external pdflatex required). `scale` takes a tier constant.

```python
title = MathTex(r"\textbf{Derivatives}", color=PRIMARY, scale=SCALE_DISPLAY)
eq    = MathTex(r"f'(x) = \lim_{h \to 0} \frac{f(x+h)-f(x)}{h}",
                color=PRIMARY, scale=SCALE_BODY)
lbl   = MathTex(r"\Delta x", color=YELLOW, scale=SCALE_LABEL)
```

**Single string, not variadic.** chalk's `MathTex(tex_string, color=..., stroke_width=..., fill_opacity=..., scale=...)` takes **one** LaTeX string. Unlike manim, there is **no** `MathTex(r"\sin", r"(", r"x^2", r")")` variadic form for indexed substrings; calling it that way binds the second positional arg to `color` and raises `TypeError: got multiple values for argument 'color'`. There is also no `tex[i]` substring accessor — the whole LaTeX renders as one VGroup of glyphs.

If you need to highlight a sub-expression, compose multiple MathTex objects with `next_to()` and animate the one you want:

```python
outer = MathTex(r"\sin", color=PRIMARY, scale=SCALE_DISPLAY)
inner = MathTex(r"x^2", color=YELLOW, scale=SCALE_DISPLAY)
close = MathTex(r")", color=PRIMARY, scale=SCALE_DISPLAY)
lparen = MathTex(r"(", color=PRIMARY, scale=SCALE_DISPLAY)
# compose: sin ( x^2 )
next_to(lparen, outer, direction="RIGHT", buff=0.05)
next_to(inner, lparen, direction="RIGHT", buff=0.05)
next_to(close, inner, direction="RIGHT", buff=0.05)
self.play(Circumscribe(inner, color=YELLOW, run_time=1.2))  # highlight the inner
```

**`tex_string` attribute** — MathTex stores the LaTeX source in `.tex_string`. `TransformMatchingTex` reads this for token matching.

**Scale tiers:** `SCALE_DISPLAY` for the one main equation per beat; `SCALE_BODY` for secondary equations; `SCALE_LABEL` for object labels; `SCALE_ANNOT` for small annotations.

**Positioning:** always use `place_in_zone` or `next_to` — never raw `move_to(x, y)` with magic numbers. See §8.

See `examples/example_01_fadein_mathtex.py` and `examples/example_02_write_equation.py`.

---

## 3. Shapes — Circle, Rectangle, Line, Arrow, Dot, Polygon

```python
circ = Circle(radius=1.0, color=BLUE, stroke_width=2.5)
rect = Rectangle(width=3.0, height=2.0, color=GREEN, stroke_width=2.0)
line = Line((-3.0, 0.0), (3.0, 0.0), color=GREY, stroke_width=1.5)
arr  = Arrow((-2.0, 0.0), (2.0, 0.0), color=PRIMARY, stroke_width=2.0)
dot  = Dot(point=(1.5, 0.8), radius=0.12, color=YELLOW)
hex6 = RegularPolygon(6, radius=1.2, color=BLUE, stroke_width=2.0)
tri  = Polygon((-1.0,-0.8),(1.0,-0.8),(0.0,1.0), color=GREEN, stroke_width=2.0)
arc  = ArcBetweenPoints((-2.0,0.0),(2.0,0.0), angle=1.57, color=YELLOW, stroke_width=2.0)
```

**`ArcBetweenPoints(start, end, angle)`:** positive `angle` means the arc curves upward (left of the direction from start→end). Use for curved arrows and curved paths.

**`Dot`:** filled circle at a point. Use for points on axes, intersection markers, orbiting bodies. Not the same as `Circle` — Dot has `fill_opacity=1.0` by default.

**`shift(dx, dy)` vs `move_to(x, y)`:** use `shift` for relative displacement, `move_to` for absolute placement (both take 2D args in chalk, unlike Manim's 3D vectors).

See `examples/example_03_shapes.py` and `examples/example_04_dot_polygon.py`.

---

## 4. Axes and plot_function — anything on a coordinate plane

```python
ax = Axes(
    x_range=(-1.0, 4.0),   # data domain
    y_range=(-1.0, 9.0),   # data range
    width=8.0,             # world-units wide
    height=5.0,            # world-units tall
    x_step=1.0,
    y_step=2.0,
    color=GREY,
)
graph = plot_function(ax, lambda x: x**2, color=BLUE, stroke_width=3.0)
```

**`ax.to_point(x, y)`** converts data coordinates to world (scene) coordinates. **Always use `to_point`; never hardcode world coordinates on an axes-anchored object.**

```python
dot_at_2 = Dot(point=ax.to_point(2.0, 4.0), radius=0.12, color=YELLOW)
```

**Sizing rule:** `width=8.0, height=5.0` fits inside `ZONE_CENTER` and leaves room for `ZONE_TOP` labels and `ZONE_BOTTOM` readouts. Wider axes push labels out of the safe area.

**Restricted domain:** `plot_function(ax, lambda x: 1/x, x_start=0.1, x_end=4.0)` — pass explicit `x_start`/`x_end` near discontinuities.

See `examples/example_07_axes_plot.py` and `examples/example_08_axes_to_point.py`.

---

## 5. ValueTracker + ChangeValue — for anything that changes continuously

`ValueTracker(v)` holds a float. `ChangeValue(tracker, target, run_time, rate_func)` animates it. Read the current value anywhere with `.get_value()`.

```python
t = ValueTracker(0.0)
self.play(ChangeValue(t, 5.0, run_time=3.0, rate_func=linear))
print(t.get_value())  # 5.0 after finish
```

**The pattern:** pair with `always_redraw` for derived visuals.

```python
x = ValueTracker(0.0)
dot = always_redraw(
    lambda: Dot(point=ax.to_point(x.get_value(), f(x.get_value())),
                radius=0.12, color=YELLOW)
)
self.add(dot)
self.play(ChangeValue(x, 3.0, run_time=3.0, rate_func=linear))
```

**`always_redraw(factory)`** calls `factory()` every frame. The returned mobject is rebuilt fresh each frame. Keep the factory cheap: no heavy VGroup construction inside tight loops; for a simple Dot or Line it's fine.

**`DecimalNumber(tracker, num_decimal_places, color, scale)`** is a pre-built `always_redraw` that shows a tracker's value as text.

```python
counter = DecimalNumber(t, num_decimal_places=1, color=PRIMARY, scale=SCALE_DISPLAY)
place_in_zone(counter, ZONE_CENTER)
self.add(counter)
self.play(ChangeValue(t, 100.0, run_time=5.0, rate_func=linear))
```

See `examples/example_09_value_tracker_decimal.py`, `examples/example_10_always_redraw.py`, `examples/example_11_change_value.py`.

---

## 6. Transform — morphing one mobject into another

`Transform(source, target, run_time, rate_func)` morphs the *source* mobject's geometry to match the *target's*. After finish, `source` is on screen with target's geometry; `target` was never added.

```python
circle = Circle(radius=0.8, color=BLUE)
square = Rectangle(width=1.6, height=1.6, color=GREEN)
self.add(circle)
self.play(FadeIn(circle, run_time=0.5))
self.play(Transform(circle, square, run_time=1.0))
# circle is now on screen with square's geometry
```

**`TransformMatchingTex(src, tgt, run_time)`** morphs LaTeX equation glyphs by token identity — shared tokens transform in place, unmatched source tokens fade out, new target tokens fade in.

```python
eq1 = MathTex(r"F = ma", color=PRIMARY, scale=SCALE_DISPLAY)
eq2 = MathTex(r"a = F/m", color=YELLOW, scale=SCALE_DISPLAY)
place_in_zone(eq1, ZONE_CENTER)
place_in_zone(eq2, ZONE_CENTER)
self.add(eq1)
self.play(Write(eq1, run_time=1.0))
self.play(TransformMatchingTex(eq1, eq2, run_time=1.5))
```

After `TransformMatchingTex`, `eq1`'s glyphs hold `eq2`'s geometry and the `/` glyph is added to the scene automatically. Do **not** add `eq2` manually — chalk handles it.

See `examples/example_05_transform.py` and `examples/example_06_transform_matching_tex.py`.

---

## 7. Motion animations — MoveAlongPath, Rotate, ShiftAnim

**`MoveAlongPath(mob, path, run_time, rate_func)`** slides `mob` along any VMobject (Circle, polygon, arbitrary curve) using arc-length parameterization.

```python
orbit = Circle(radius=2.0, color=GREY, stroke_width=1.0)
probe = Dot(point=(2.0, 0.0), radius=0.12, color=YELLOW)
self.add(orbit, probe)
self.play(MoveAlongPath(probe, orbit, run_time=4.0, rate_func=linear))
```

**`Rotate(mob, angle, about_point, run_time, rate_func)`** rotates `mob` around a world point.

```python
sq = Rectangle(width=2.0, height=2.0, color=BLUE)
self.play(Rotate(sq, angle=2*math.pi, about_point=(0.0,0.0), run_time=4.0, rate_func=linear))
```

**`ShiftAnim(mob, dx, dy, run_time)`** slides `mob` by `(dx, dy)` world units.

```python
self.play(ShiftAnim(ball, dx=5.0, dy=0.0, run_time=2.0))
```

---

## 8. Animation composition — AnimationGroup, LaggedStart, Succession

**`AnimationGroup(*anims, lag_ratio)`** runs animations with a staggered offset. `lag_ratio=0` = fully parallel; `lag_ratio=1` = back-to-back (Succession); `lag_ratio=0.3` is the typical stagger.

```python
self.play(
    AnimationGroup(
        FadeIn(a, run_time=0.6),
        FadeIn(b, run_time=0.6),
        FadeIn(c, run_time=0.6),
        lag_ratio=0.3,
    )
)
```

**`LaggedStart(*anims, lag_ratio=0.3)`** is shorthand for `AnimationGroup` with `lag_ratio=0.3`.

**`Succession(*anims)`** runs animations strictly one after another (`lag_ratio=1`).

**Estimating play() wall-clock duration with lag_ratio:** the total time a `self.play(AnimationGroup(...))` takes is **not** `sum(run_times)`. The last animation starts `(N−1) × lag_ratio × mean(run_time)` into the group, then runs for its own `run_time`. Approximate:

```
play_duration ≈ max(run_time) + (N - 1) × lag_ratio × mean(run_time)
```

Examples:
- `AnimationGroup(3 × FadeIn(run_time=1.0), lag_ratio=0.3)` → play ≈ `1.0 + 2 × 0.3 × 1.0` = `1.6s`. (Not `3.0s`.)
- `AnimationGroup(4 × FadeIn(run_time=1.2), lag_ratio=0.25)` → play ≈ `1.2 + 3 × 0.25 × 1.2` = `2.1s`.
- `Succession(3 × FadeIn(run_time=1.0))` (lag_ratio=1.0) → play ≈ `3.0s`.
- `AnimationGroup(3 × FadeIn(run_time=1.0), lag_ratio=0.0)` → play ≈ `1.0s`. Fully parallel.

Budget `self.wait(x)` values against this, not against the naive sum. Under-estimating play duration is fine (wait absorbs it); over-estimating means the scene runs short of its `target_duration_seconds`.

---

## 9. Emphasis animations — Indicate, Flash, Circumscribe

```python
self.play(Indicate(mob, scale_factor=1.2, color=YELLOW, run_time=0.8))
self.play(Flash((0.0, 0.0), color=YELLOW, num_lines=10, line_length=0.3, run_time=0.5))
self.play(Circumscribe(mob, shape="rect", color=BLUE, buff=0.2, run_time=0.8))
```

`Flash` takes a `(x, y)` point, not a mobject. `Indicate` pulses with scale and recolor then restores. `Circumscribe` draws an animated outline (rect or circle) around the mobject's bounding box.

**Flash mobjects must be pre-added to the scene** before playing (unlike most animations):

```python
f = Flash((1.0, 0.0), color=YELLOW, run_time=0.5)
for m in f.mobjects:
    self.add(m)
self.play(f)
```

---

## 10. Layout — place_in_zone, next_to, labeled_box, arrow_between, brace_label

**Frame:** 14.2 × 8.0 world units. Safe area: x ∈ [−6.6, 6.6], y ∈ [−3.5, 3.5].

**Zones:**
- `ZONE_TOP = (2.0, 3.5)` — beat title, law statement (y-center ≈ 2.75)
- `ZONE_CENTER = (−2.0, 2.0)` — main visual (y-center ≈ 0.0)
- `ZONE_BOTTOM = (−3.5, −2.0)` — running step, result caption (y-center ≈ −2.75)

```python
place_in_zone(mob, ZONE_TOP)     # centers mob horizontally inside the zone's y band
place_in_zone(mob, ZONE_CENTER)  # most-used
place_in_zone(mob, ZONE_BOTTOM)
```

**Zone-collision rule — critical.** After `place_in_zone(title, ZONE_TOP)`, do NOT then `move_to(0.0, 2.2)` a second element: `y = 2.2` is still inside ZONE_TOP's band (2.0, 3.5) and collides with the title. Same mistake patterns:

| Mistake | Why it fails |
|---|---|
| Title at ZONE_TOP + second element at `y=2.2` | `2.2` is inside ZONE_TOP (2.0, 3.5) — overlap |
| Formula at ZONE_CENTER + mantra at `y=−0.8` | Both inside ZONE_CENTER (−2.0, 2.0) — vertical overlap unless explicitly offset by bbox-height + buff |
| Payoff at ZONE_BOTTOM + caption at `y=−2.2` | `−2.2` is inside ZONE_BOTTOM (−3.5, −2.0) — overlap |

Safe pattern: within a single zone, the **first** placement uses `place_in_zone`; any **additional** elements in that zone use `next_to(second, first, direction="DOWN"|"UP", buff=0.35)`. That way the second element's position is computed from the first element's bbox, not a magic y-number that may fall inside a neighbouring zone.

If you need two elements stacked vertically in the same semantic band, use `next_to(..., direction="DOWN", buff=0.35)` — never two `move_to`s with hand-picked ys.

**`next_to(mob, anchor, direction, buff)`** — position `mob` relative to `anchor`'s bounding box.

```python
next_to(label, circle, direction="UP", buff=0.3)
next_to(caption, eq, direction="DOWN", buff=0.4)
```

**`labeled_box(label_latex, color, scale=0.55, pad_x=0.5, pad_y=0.35, ...)`** — auto-sizes a Rectangle around the rendered LaTeX label. Never hand-size.

Signature returns a **tuple** `(box, label)` — you must unpack it. Both are centered at origin; the caller shifts them together (or wraps them in a VGroup and shifts the group). The first arg is a **raw LaTeX string**, not a MathTex object.

```python
box, lbl = labeled_box(r"\mathrm{Agent}", color=GREY, scale=SCALE_LABEL)
# Move them together:
box.shift(2.0, 0.0)
lbl.move_to(2.0, 0.0)
self.add(box, lbl)

# Or group them for single-shift movement:
group = VGroup(box, lbl)
group.shift(2.0, 0.0)
self.add(group)
```

**Anti-patterns:**
- `labeled_box(MathTex(r"..."), ...)` — first arg is a string, not a MathTex. Passing a MathTex raises TypeError.
- `box = labeled_box(...)` (single-var unpack) — returns tuple; you lose the label.
- Shifting only one of `(box, lbl)` — they decouple and the label slides off.

**`arrow_between(src, tgt, buff, color)`** — anchors Arrow at bbox edges. Never hand-pick start/end coords. Accepts any VMobject (Circle/Rectangle/Line/Arrow/Dot) or VGroup (MathTex, nested composites) on either side — bbox computation recurses through nested VGroups.

**`brace_label(mob, tex, direction, color, scale)`** — Brace + label positioned at tip.

```python
brace, blbl = brace_label(segment, r"\Delta x = 3", direction="UP",
                           color=YELLOW, scale=SCALE_LABEL)
self.add(brace, blbl)
self.play(FadeIn(brace, run_time=0.4), FadeIn(blbl, run_time=0.4))
```

---

## 11. Scene structure — the mandatory pattern

```python
class MyScene(Scene):
    def construct(self):
        # ── Beat 0: title ─────────────────────────────────────────
        self.section("title")
        title = MathTex(r"\text{Topic}", color=PRIMARY, scale=SCALE_DISPLAY)
        place_in_zone(title, ZONE_CENTER)
        self.add(title)
        self.play(Write(title, run_time=1.2))
        self.wait(2.0)
        self.clear(run_time=0.5)

        # ── Beat 1: main content ──────────────────────────────────
        self.section("beat1")
        lbl = MathTex(r"\text{Step 1}", color=YELLOW, scale=SCALE_BODY)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))
        # ... content ...
        self.wait(2.0)
        self.clear(run_time=0.4)

        # ── Beat 2: result ────────────────────────────────────────
        self.section("result")
        # ... last beat (no clear at end) ...
        self.wait(3.0)
```

**Rules:**
- `self.clear()` after every beat except the last.
- Every mobject must `FadeIn` or `Write` after `self.add()` — never pop in.
- `self.section(name)` marks the timeline for TTS sync.
- At most 4 active semantic color slots per beat.
- At most 3 zones active in any rest frame.

---

## Timing conventions

| Verb | Default run_time |
|---|---|
| `Write` (title, ≤ 20 chars) | 0.8–1.2 s |
| `Write` (equation, ≤ 40 chars) | 1.2–1.8 s |
| `FadeIn` / `FadeOut` (element) | 0.4–0.6 s |
| `FadeIn` / `FadeOut` (title) | 0.6–0.8 s |
| `Transform` / `TransformMatchingTex` | 1.0–1.8 s |
| `ChangeValue` sweep | matches narration (explicit always) |
| `ShiftAnim` motion | 2.0–3.5 s |
| `MoveAlongPath` orbit | 4.0–6.0 s |
| `Rotate` full turn | 3.0–5.0 s |
| `Indicate` | 0.6–0.8 s |
| `Circumscribe` | 0.6–1.0 s |
| `self.clear()` | 0.4–0.5 s |
| Hold after reveal | ≥ 0.8 s |
| Final hold | ≥ 2.0 s |

---

## Examples

17 runnable scenes under `examples/`. Each file contains exactly one `Scene` subclass.

| # | File | Demonstrates |
|---|---|---|
| 01 | `example_01_fadein_mathtex.py` | FadeIn on MathTex at each scale tier |
| 02 | `example_02_write_equation.py` | Write on a display equation |
| 03 | `example_03_shapes.py` | Circle, Rectangle, Line, Arrow |
| 04 | `example_04_dot_polygon.py` | Dot, Polygon, RegularPolygon, ArcBetweenPoints |
| 05 | `example_05_transform.py` | Transform between Circle and Rectangle |
| 06 | `example_06_transform_matching_tex.py` | TransformMatchingTex: F=ma → a=F/m |
| 07 | `example_07_axes_plot.py` | Axes + plot_function parabola |
| 08 | `example_08_axes_to_point.py` | ax.to_point() + Dot placed at data coord |
| 09 | `example_09_value_tracker_decimal.py` | ValueTracker + DecimalNumber counter |
| 10 | `example_10_always_redraw.py` | always_redraw dot tracking a ValueTracker |
| 11 | `example_11_change_value.py` | ChangeValue sweep with linear rate |
| 12 | `example_12_move_along_path.py` | MoveAlongPath on a Circle |
| 13 | `example_13_rotate.py` | Rotate a square one full turn |
| 14 | `example_14_animation_group.py` | AnimationGroup, LaggedStart, Succession |
| 15 | `example_15_emphasis.py` | Indicate, Flash, Circumscribe |
| 16 | `example_16_number_line_brace.py` | NumberLine + brace_label |
| 17 | `example_17_layout.py` | place_in_zone, next_to, labeled_box, arrow_between |

---

## Gotchas / anti-patterns

- **Raw hex color in scene file.** Use palette constants. `color="#4FC3F7"` → `color=BLUE`.
- **Magic-number scale.** `scale=0.5` → `scale=SCALE_LABEL`.
- **`MathTex(color=RED_FILL)`.** RED_FILL fails text contrast. For a red element's label, use `PRIMARY` and rely on proximity.
- **`self.add(mob)` with no FadeIn.** Viewer gets no cue. Always follow `add` with `FadeIn` or `Write`.
- **Hardcoded coordinates on axes-anchored objects.** `Dot(point=(2.0, 4.0))` is a scene-coord placement; `Dot(point=ax.to_point(2.0, 4.0))` follows the axes. Use `to_point` always.
- **Adding eq2 before `TransformMatchingTex`.** Don't add the target MathTex to the scene; chalk adds only the new glyphs automatically.
- **Flash without pre-adding mobjects.** Flash lines must be `self.add(m)` before `self.play(flash)`.
- **Hand-sizing a Rectangle around text.** Use `labeled_box()`.
- **Hand-picking Arrow start/end coords.** Use `arrow_between()`.
- **Overloaded scenes.** More than 4 active color semantics or more than 3 zones → cognitive overload. Split the beat.
- **`ChangeValue` run_time = None.** Always pass an explicit `run_time` to ChangeValue; it has no default relationship to narration length.

---

## Changelog

- **0.1.0** (2026-04-21) — initial ship. Replaces `manim-primitives` per ADR 0001 (chalk replaces Manim). 17 runnable examples across MathTex, shapes, Axes, ValueTracker, Transform, motion animations, animation composition, emphasis, and layout helpers.
