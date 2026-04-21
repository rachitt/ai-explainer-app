---
name: manim-primitives
version: 0.1.0
category: manim
triggers:
  - stage:manim-code
  - stage:manim-repair
  - scene_type:any
requires:
  - scene-spec-schema@^0.1.0
token_estimate: 5100
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  The six Manim Community primitives every scene is built from — Write, Create,
  Transform, MathTex, Axes, ValueTracker — with runnable examples and the
  timing, composition, and API conventions the Manim-code agent needs to emit
  working code on the first pass. Loaded by the Manim-code agent on every
  scene; loaded by the Manim-repair agent on every retry. Consulting it before
  reaching for a less-common class is the difference between a 100-line scene
  that compiles and a 300-line scene that doesn't.
---

# manim-primitives

## Purpose

Phase 1 scenes are assembled almost entirely from six Manim Community classes. Mastering these six is 90% of the job; the rest is composition. This skill documents them with runnable examples and the conventions the Manim-code agent should follow — idiomatic uses, common mistakes, and the timing math that makes `run_time` estimates consistent with the visual planner's pacing.

Every example in `examples/` is a complete, runnable `Scene` with no external imports beyond `manim`. Rendering any example via `manim -ql examples/example_NN.py <SceneName>` should produce an MP4 with no stderr output. If an example ever fails to render in CI, the skill ships broken.

## When to load

- **Manim-code agent — always.** Every scene uses at least one of these primitives.
- **Manim-repair agent — always.** Repair needs the same vocabulary as the original call.
- **Visual-planner — no.** The planner works in terms of scene-spec animation verbs (`fade_in`, `transform_to`), not Manim classes. Classes are an implementation concern.

## Core content

### 1. Write — for text and math that should "draw itself in"

`Write` animates by tracing strokes and filling in. Use for text that should feel authored: titles, labels, equation reveals. The camera's default `run_time` is 1.0s; longer text scales automatically (`Write` uses `lag_ratio=0.5` internally, so a 20-character line takes ~1.5s; a 60-character line ~2.5s).

```python
self.play(Write(Text("Derivatives")))                # ~1.0s
self.play(Write(MathTex(r"\frac{df}{dx}")))          # ~1.0s
self.play(Write(title, run_time=0.6))                # force faster
```

**When to reach for something else:**
- For a list of bullets, use `Write` on each in sequence with `lag_ratio=0.3` (see example 02) — one-shot `Write` on a VGroup feels mechanical.
- For math that should *morph* from a previous equation, use `TransformMatchingTex` (example 11), not `Write` on the new one.

### 2. Create — for shapes and curves

`Create` animates an outline being drawn. Use for geometric shapes, graph curves, arrows. `DrawBorderThenFill` is a filled variant (outline first, then fill) — use it when the final shape should be solid but the construction should feel deliberate.

```python
self.play(Create(Circle()))                          # outline draws around
self.play(DrawBorderThenFill(Square(fill_opacity=1)))# outline, then fill
self.play(Create(ax.plot(lambda x: x**2)))           # parabola draws in
```

**Rule of thumb:**
- Line-art (axes, vectors, unfilled polygons) → `Create`.
- Filled region (rectangle for Riemann sum, shaded area) → `DrawBorderThenFill`.
- Graph of a function → `Create`. Let the curve sweep in left-to-right; the eye tracks it naturally.

### 3. Transform — for morphing one mobject into another

Three flavours, easily confused:

| Animation | What it does | When to use |
|---|---|---|
| `Transform(a, b)` | Animates `a` → shape/position/color of `b`. After: `a` is on screen holding `b`'s state; `b` was never added. | When you want to keep the original reference alive (reuse `a`'s name later). |
| `ReplacementTransform(a, b)` | Animates `a` → `b`. After: `a` is removed, `b` is on screen. | Default for most cases. Cleaner mental model: "`a` becomes `b`, then we work with `b`." |
| `TransformMatchingShapes(a, b)` | Morphs shared sub-shapes in place; unmatched parts fade. | Geometric morphs where you haven't hand-indexed substrings. |
| `TransformMatchingTex(a, b)` | Like above, but matches by LaTeX substring. | Equation edits: `x+1` → `x+1+dx`. Works best when both sides share literal substrings. |

**Pitfall:** `Transform(a, b)` after which you call `self.play(a.animate.shift(UP))` — that shifts *the post-transform* `a`, not the original. Half the Manim surprises come from this. If you'll manipulate the result, use `ReplacementTransform`.

### 4. MathTex — for every formula

`MathTex(r"...")` renders LaTeX math. `Tex(r"...")` renders LaTeX text (no math-mode delimiters needed, math inside `$...$`). For Phase 1, use `MathTex` for display equations, `Tex` only when you need inline prose mixing text and math.

```python
eq = MathTex(r"\frac{d}{dx}", r"x^2", r"=", r"2x")   # 4 substrings, indexable
eq[1].set_color(YELLOW)                              # colour just x^2
```

**Substring indexing is the single highest-leverage MathTex feature.** Pass a list of strings; each becomes `eq[i]`. Colour, transform, or annotate individual pieces. See `latex-for-video` for the full patterns.

**Gotchas:**
- `r"..."` raw strings always. Regular strings mangle `\`.
- `MathTex` requires a LaTeX install (`pdflatex` + `dvisvgm`). On macOS: `brew install --cask basictex` then `sudo tlmgr install standalone preview` (see `manim-debugging` entry `latex-missing-package`).
- LaTeX errors are compile-time; expect a 2–3s first-compile then ~0.5s per subsequent call (cached).

### 5. Axes — for anything on a coordinate plane

`Axes(x_range=[a,b,step], y_range=[c,d,step])` is the workhorse. `ax.plot(f)` draws a function; `ax.c2p(x, y)` maps data coordinates to scene coordinates; `ax.get_graph_label(graph, "f(x)=x^2")` places a label that follows the curve.

```python
ax = Axes(x_range=[-1, 4, 1], y_range=[-1, 9, 2], x_length=7, y_length=4)
parabola = ax.plot(lambda x: x**2, color=BLUE)
dot = Dot(ax.c2p(2, 4))                              # at data point (2, 4)
```

**Two axes-specific rules:**
- Always pass explicit `x_length`/`y_length`. Default sizing produces axes that overflow the frame on tall y-ranges.
- Use `ax.c2p(x, y)` to place anything on the axes, never raw coordinates. If the axes get rescaled, `c2p`-placed objects follow; raw-coordinate ones don't.
- `ax.plot(lambda x: 1/x)` will crash at `x=0`. Pass `use_smoothing=False` near discontinuities and restrict `x_range`.

`NumberPlane` is a subclass of `Axes` with a grid; use it when the grid itself is pedagogically meaningful (transformations demo, complex plane).

### 6. ValueTracker — for anything that changes continuously

A `ValueTracker` holds a float you can animate. Coupled with `add_updater`, it drives continuous change of other mobjects: a moving dot, a tangent line whose slope follows `x`, a counter whose value follows an integration.

```python
x = ValueTracker(0)
dot = always_redraw(lambda: Dot(ax.c2p(x.get_value(), f(x.get_value()))))
self.add(dot)
self.play(x.animate.set_value(3), run_time=3)        # 3s sweep
```

Two APIs for tying a mobject to a tracker:

- **`always_redraw(lambda: ...)`** — re-evaluates the lambda every frame. Simple; safe. Prefer this.
- **`.add_updater(lambda m: ...)`** — more control; updater mutates the mobject in place. Use when `always_redraw` allocates too much (e.g., rebuilding a `DecimalNumber` each frame is fine, but rebuilding a complex VGroup is not).

**Remove updaters before the scene ends** or the final frame renders with stale updater state:

```python
dot.clear_updaters()
```

**Pattern (the one you'll reach for 80% of the time):** one `ValueTracker` per animated parameter, `always_redraw` for all derived visuals, `self.play(x.animate.set_value(target), run_time=…)` to drive it. This is the spine of `manim-calculus-patterns` (tangent tracker, Riemann-sum parameter, ε-δ window width).

## Cross-cutting conventions

### Timing

Budget per animation verb, assuming 1× rate (from `pacing-rules`):

| Verb | Default `run_time` | Notes |
|---|---|---|
| Short `Write` (≤ 20 chars) | 1.0 | Scales with text length. |
| Long `Write` (≤ 80 chars) | 2.0 | |
| `Create` (shape) | 1.0 | |
| `Create` (function curve on axes) | 1.5 | Longer feels more deliberate. |
| `Transform` / `ReplacementTransform` | 1.0 | |
| `FadeIn` / `FadeOut` | 0.5 | |
| `x.animate.set_value(…)` sweep | matches narration | Explicit `run_time` always. |

When the narration-estimated scene duration is, say, 12s and the sum of default run_times is 8s, the visual planner should either stretch individual verbs or insert `self.wait(0.5)` between them — don't speed up `Write` to <0.6s, the stroke trace becomes illegible.

### Composition: VGroup

A `VGroup` is a Manim mobject whose children move/scale/colour as one. Canonical use:

```python
axes_group = VGroup(ax, graph, label)
self.play(axes_group.animate.shift(LEFT * 2))
```

A scene with more than 4 top-level mobjects is usually a scene that should be factored into VGroups. See `scene-composition` §7 for the grouping rules.

### Coordinate conventions

- Manim default frame: 14 units wide × 8 units tall, origin at centre. `UP = [0,1,0]`, `RIGHT = [1,0,0]`; `UL = UP+LEFT`; etc.
- `.next_to(other, direction, buff=0.3)` is almost always better than raw coordinates. `.to_edge(UP, buff=0.5)` places against an edge with a margin.
- `c2p` (coords-to-point) on an `Axes` converts data space → scene space. Never mix them.

### The rendering incantation

Every example renders with:

```bash
cd pedagogica/skills/knowledge/manim-primitives/examples
uv run manim -ql example_01_write_text.py WriteText
# output: media/videos/example_01_write_text/480p15/WriteText.mp4
```

`-ql` is 480p15, the CI / dev default. `-qm` is 720p30 (preview quality). `-qh` is 1080p60 (final, never use in authoring). Bumping quality never fixes a bug; it just slows the loop.

## Examples

17 runnable scenes under `examples/`. Each file contains exactly one `Scene` subclass named in PascalCase; the filename is `example_NN_snake_case.py`.

| # | File | Primitive | Demonstrates |
|---|---|---|---|
| 01 | `example_01_write_text.py` | Write | Single `Write` on a `Text`. The minimal hello-world. |
| 02 | `example_02_write_bullet_list.py` | Write | Sequential `Write` on a VGroup of lines via `lag_ratio`. |
| 03 | `example_03_create_circle.py` | Create | `Create` on a `Circle`. |
| 04 | `example_04_draw_border_then_fill.py` | Create | `DrawBorderThenFill` on a filled rectangle (Riemann bar shape). |
| 05 | `example_05_transform_circle_to_square.py` | Transform | `Transform(circle, square)` — reference stays as `circle`. |
| 06 | `example_06_replacement_transform.py` | Transform | `ReplacementTransform` — post-animation reference is the new mobject. |
| 07 | `example_07_transform_matching_shapes.py` | Transform | Structural morph between two polygons. |
| 08 | `example_08_mathtex_basic.py` | MathTex | Simple `MathTex`, requires LaTeX. |
| 09 | `example_09_mathtex_substring_colors.py` | MathTex | Indexed substrings coloured independently. |
| 10 | `example_10_mathtex_transform_matching_tex.py` | MathTex | Equation edit via `TransformMatchingTex`. |
| 11 | `example_11_axes_basic.py` | Axes | `Axes` + `plot` + `c2p` dot placement. |
| 12 | `example_12_axes_graph_label.py` | Axes | `get_graph_label` — label follows the curve. |
| 13 | `example_13_axes_moving_dot.py` | Axes | Dot animated along a graph via `MoveAlongPath`. |
| 14 | `example_14_value_tracker_basic.py` | ValueTracker | `ValueTracker` + `DecimalNumber` counter. |
| 15 | `example_15_value_tracker_always_redraw.py` | ValueTracker | `always_redraw` for a dot on a graph. |
| 16 | `example_16_value_tracker_updater.py` | ValueTracker | `.add_updater` for a tangent line. |
| 17 | `example_17_vgroup_coordination.py` | VGroup | Axes + graph + label grouped and shifted together. |

Examples 08, 09, 10 require a LaTeX install. The rest render with just `manim + ffmpeg`.

## Gotchas / anti-patterns

- **Using `Tex` when `MathTex` is what you mean.** `Tex(r"x^2")` renders `x^2` as text with literal `^`. Use `MathTex`.
- **Calling `.get_graph()` on `Axes`.** Renamed to `.plot()` in Manim ≥ 0.18. Error catalog entry in `manim-debugging`.
- **Forgetting `c2p` on the first dot placement.** `Dot([2, 4, 0])` places at scene coord (2,4), not data coord. Always `ax.c2p(2, 4)`.
- **Long `run_time` on `Write`.** Writing animations over 3s are tedious. If the text is that long, the scene is over-stuffed — shrink the text.
- **One giant `self.play(*many, …)` call.** Manim will honour it but the viewer can't parse 8 simultaneous animations. Max 3 concurrent animations in one `play` call.
- **`always_redraw` with a heavy body.** Rebuilding a VGroup with 100 submobjects 30 times a second tanks render time. Use `.add_updater` and mutate in place.
- **Updaters left attached past the animation.** The final scene frame freezes with the updater still wiring; exports can show a phantom shimmer. Call `.clear_updaters()` before the scene ends.
- **Raw floats in coordinates.** Manim expects 3D vectors even for 2D scenes: `dot.move_to([1, 2, 0])`, not `dot.move_to([1, 2])`.
- **`Transform` when you'll keep using the reference.** See §3 pitfall. `ReplacementTransform` is the safe default.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. 17 runnable examples across Write, Create, Transform, MathTex, Axes, ValueTracker. Timing table, VGroup conventions, rendering incantation. Paired with `scene-spec-schema` and consumed by `manim-code`/`manim-repair` agents.
