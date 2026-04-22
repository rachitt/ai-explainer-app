---
name: chalk-calculus-patterns
version: 0.1.0
category: chalk
triggers:
  - domain:calculus
  - stage:visual-planner
  - stage:chalk-code
  - stage:chalk-repair
requires:
  - scene-spec-schema@^0.1.0
  - chalk-primitives@^0.1.0
  - latex-for-video@^0.1.0
  - color-and-typography@^0.1.0
token_estimate: 7200
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-21
description: >
  Ten canonical chalk patterns for calculus explainer scenes — derivative as
  slope (secant → tangent), moving tangent tracker, left Riemann sum, Riemann →
  integral limit, ε-δ window, chain rule nested boxes, FTC area accumulator,
  function shift/scale, product rule as a box, and related rates (balloon).
  Each pattern is a runnable chalk Scene plus a note on which SceneBeat shapes
  it serves. Loaded by the visual planner when scene_beat.domain == calculus and
  by the chalk-code agent on every calculus codegen. Replaces
  manim-calculus-patterns as of 2026-04-21 per ADR 0001.
---

# chalk-calculus-patterns

## Purpose

Undergraduate calculus has ten-odd visual moves that keep showing up: a tangent line that follows a point, a stack of rectangles approximating an area, an ε-ball shrinking around a limit. 3Blue1Brown and Khan Academy reuse these moves; so do we.

This skill catalogues the ten patterns as chalk scenes. Each is written so the visual planner can read the scene structure and the chalk-code agent can adapt it — substituting the specific function, interval, or parameters the topic calls for. Patterns are worked examples, not templates.

Every example in `examples/` runs with `uv run chalk examples/pattern_NN_… -s ClassName -o /tmp/out.mp4 --width 1280 --height 720` from the `chalk/` directory. No external LaTeX install required.

## When to load

- **Visual planner — when `scene_beat.domain == calculus`.** Consult to pick which pattern fits and generate concrete `animation_plan` entries.
- **chalk-code agent — always for calculus scenes.** Pattern examples carry run-time budgets, `ax.to_point()` usage, and `always_redraw` / `ChangeValue` idioms.
- **chalk-repair — on retry.** Often "this should have been pattern X". Load the pack for reference comparison.
- **Not needed by:** storyboard, script, TTS, editor, subtitle.

## Colour semantics for calculus scenes

| Role | Constant | Notes |
|---|---|---|
| Main curve | `BLUE` | The function being discussed |
| Moving point / dot | `YELLOW` | The thing that moves or is highlighted |
| Area / integral region | `GREEN` | Shading under a curve |
| Tangent / slope indicator | `PRIMARY` | The derivative visualization |
| Secondary curve | `GREY` | Reference curve, comparison, envelope |
| Axis / annotation | `GREY` | Tick labels, braces, brackets |

These override the default palette semantics only for calculus scenes. See `color-and-typography` for the full palette.

## Axes sizing rule

`Axes(width=8.0, height=5.5)` fits in `ZONE_CENTER` and leaves room for `ZONE_TOP` beat labels and `ZONE_BOTTOM` readouts. Narrow x-ranges (0–4) → keep width=7.0 to avoid wasted space.

Always use `ax.to_point(x, y)` to place anything on axes. Never hand-code world coordinates for axes-anchored objects.

## Pattern index

| # | Pattern | File | Beat type | Key mechanic |
|---|---|---|---|---|
| 01 | Derivative as slope (secant → tangent) | `pattern_01_derivative_slope.py` | `define`, `hook` | Two dots + secant; drive h→0 |
| 02 | Tangent line tracker | `pattern_02_tangent_tracker.py` | `example`, `generalize` | always_redraw tangent, ChangeValue x |
| 03 | Left-Riemann sum | `pattern_03_riemann_left.py` | `example` | N rectangles, LaggedStart cascade |
| 04 | Riemann → integral limit | `pattern_04_riemann_to_integral.py` | `generalize` | N steps 4→64, TransformMatchingTex Σ→∫ |
| 05 | ε-δ limit window | `pattern_05_epsilon_delta.py` | `define`, `motivate` | Two always_redraw bands, drive ε→small |
| 06 | Chain rule boxes | `pattern_06_chain_rule_boxes.py` | `example` | Nested labeled_box, arrow_between |
| 07 | FTC area accumulator | `pattern_07_ftc_accumulator.py` | `example`, `generalize` | always_redraw shaded area + A(x) dot |
| 08 | Function transformation | `pattern_08_function_transform.py` | `example` | Transform graph on fixed axes |
| 09 | Product rule as a box | `pattern_09_product_rule_box.py` | `example` | Rectangle sides u, v; strip areas |
| 10 | Related rates balloon | `pattern_10_related_rates.py` | `example` | always_redraw Circle(r), DecimalNumber |

---

## Pattern 01 — Derivative as slope (secant → tangent)

**Idea.** Two dots on a curve connected by a secant. Display slope = rise/run. Drive h → 0: the second dot slides toward the first, the secant rotates into the tangent, and the slope readout converges to the derivative value.

**Key mechanics.**
- `ValueTracker(h)` for the gap. Two `always_redraw` dots at `x₀` and `x₀+h`.
- `always_redraw` on the secant `Line` reading both dot world positions.
- `always_redraw` on a slope `DecimalNumber` reading `(f(x₀+h)-f(x₀))/h`.
- Drive `ChangeValue(h, 0.01, run_time=3.0, rate_func=smooth)`. Don't go to exactly 0 (division by zero).

**Run-time budget.** ~12s: curve draw 1.5s, dots/secant place 1s, sweep 3s, beat on result 2.5s, holds.

See `examples/pattern_01_derivative_slope.py`.

---

## Pattern 02 — Tangent line tracker

**Idea.** A dot and a tangent line move continuously along a curve, driven by a single `ValueTracker(x)`. A slope readout updates in sync.

**Key mechanics.**
- `always_redraw` for the dot: `Dot(point=ax.to_point(x.get_value(), f(x.get_value())))`.
- `always_redraw` for the tangent: a short `Line` centered on the dot with slope `f_prime(x.get_value())`. Half-length 1.2 world units.
- `always_redraw` for a `DecimalNumber` showing the current slope.
- Drive `ChangeValue(x, x_end, run_time=4.0, rate_func=linear)`.

**Run-time budget.** ~10s: curve 1.5s, tracker setup 1s, sweep 4s, hold 2s.

See `examples/pattern_02_tangent_tracker.py`.

---

## Pattern 03 — Left-Riemann sum

**Idea.** N left-endpoint rectangles under a curve approximate the area. Label the sum.

**Key mechanics.**
- `[Rectangle(width=dx, height=f(xᵢ), ...) for i in range(N)]` in world coords.
- Place each via: `rx, ry = ax.to_point(xᵢ, 0.0)` → shift rect to that anchor.
- `fill_color=GREEN, fill_opacity=0.4, stroke_color=GREEN, stroke_width=1.5`.
- Reveal via `LaggedStart(*[FadeIn(r) for r in rects], lag_ratio=0.08)`.
- N = 8 is the visual sweet spot for clarity.

**Run-time budget.** ~8s: curve 1.5s, rects cascade 1.5s, label 1s, hold 2s.

See `examples/pattern_03_riemann_left.py`.

---

## Pattern 04 — Riemann → integral limit

**Idea.** N = 4 → 8 → 16 → 64 rectangles converge to the integral. The label Σ morphs to ∫.

**Key mechanics.**
- For each N, build a new VGroup of rectangles. Use `FadeOut` old + `FadeIn` new (Transform on VGroups with different lengths is unreliable).
- `TransformMatchingTex` on `r"\sum_{i=1}^{N} f(x_i)\,\Delta x"` → `r"\int_a^b f(x)\,dx"`.
- Do not try to continuously sweep N; stepped transitions at {4, 8, 16, 64} read more clearly.

**Run-time budget.** ~14s: 4 N-steps × 1.5s + label morph 1.5s + holds 4s.

See `examples/pattern_04_riemann_to_integral.py`.

---

## Pattern 05 — ε-δ limit window

**Idea.** Shrink a horizontal band (ε-window around L) and watch the required vertical band (δ-window around a) shrink in response.

**Key mechanics.**
- `ValueTracker(eps)`. `delta` is computed from `eps` via the function's local behavior.
- Two `always_redraw` rectangles (horizontal ε-band, vertical δ-band) in different colors.
- Drive `ChangeValue(eps, 0.2, run_time=4.0, rate_func=smooth)`.
- Use `fill_opacity=0.25` for the band fills; stroke to mark the edges.

**Run-time budget.** ~14s: setup 4s, shrink 4s, second shrink 4s, hold 2s.

See `examples/pattern_05_epsilon_delta.py`.

---

## Pattern 06 — Chain rule composition (nested boxes)

**Idea.** f(g(x)) as two nested `labeled_box` blocks. Input x enters g-box, g(x) exits, enters f-box, outputs f(g(x)). Then: dx → g'(x)dx → f'(g(x))·g'(x)·dx.

**Key mechanics.**
- `labeled_box(r"\mathrm{g}", ...)` and `labeled_box(r"\mathrm{f}", ...)`.
- `arrow_between` for the flow arrows (never hand-pick coords).
- `TransformMatchingTex` for the derivative step: output label morphs from `f(g(x))` to `f'(g(x))\cdot g'(x)\cdot dx`.

**Run-time budget.** ~12s.

See `examples/pattern_06_chain_rule_boxes.py`.

---

## Pattern 07 — FTC area accumulator

**Idea.** A shaded region under f(t) grows as a vertical line sweeps from `a` to `x`. Below, a second axes plots A(x) = ∫ₐˣ f(t)dt. Visual statement: A'(x) = f(x).

**Key mechanics.**
- `ValueTracker(x_val)`. `always_redraw` on:
  - The vertical sweep line: `Line(ax.to_point(x_val, y_min), ax.to_point(x_val, f(x_val)))`.
  - The shaded area: rebuild a `VMobject` tracing the region boundary each frame (or use a filled polygon approximation at N=60 samples up to `x_val`).
  - A `Dot` on the accumulator axes: `Dot(point=ax2.to_point(x_val, A(x_val)))`.
- **Pre-compute** `A(x)` as a numerical antiderivative array before the animation. Do not call scipy inside `always_redraw`.
- Drive `ChangeValue(x_val, b, run_time=5.0, rate_func=linear)`.

**Run-time budget.** ~16s.

See `examples/pattern_07_ftc_accumulator.py`.

---

## Pattern 08 — Function transformation (shift / scale)

**Idea.** y = f(x) morphs through vertical shift, horizontal shift, vertical scale, horizontal scale. Each morph is a `Transform` on the graph VMobject.

**Key mechanics.**
- Axes fixed. Graph is the thing that transforms.
- Build each new graph with `plot_function(ax, transformed_f)`.
- `Transform(old_graph, new_graph, run_time=1.2)`.
- Label each transformation: `MathTex(r"y = f(x) + 2", ...)` replaces previous via `TransformMatchingTex`.

**Run-time budget.** ~14s: 4 transforms × 1.5s + label morphs + holds.

See `examples/pattern_08_function_transform.py`.

---

## Pattern 09 — Product rule as a box

**Idea.** Rectangle with sides u and v, area = uv. Extend u→u+du, v→v+dv. New area = old + v·du strip + u·dv strip + tiny du·dv corner (→0). Therefore d(uv) = v·du + u·dv.

**Key mechanics.**
- Main `Rectangle`, then three smaller `Rectangle`s for the strips (different colors, `fill_opacity=0.5`).
- `LaggedStart` for the strip reveals.
- Labels via `next_to` on each strip; `TransformMatchingTex` for the final formula step.
- Fade the `du·dv` corner last.

**Run-time budget.** ~14s.

See `examples/pattern_09_product_rule_box.py`.

---

## Pattern 10 — Related rates balloon

**Idea.** A balloon (circle) inflates at constant dV/dt. The radius grows non-linearly. Show r growing, V growing, dr/dt decreasing.

**Key mechanics.**
- `ValueTracker(r)` driven by `ChangeValue(r, 2.0, run_time=5.0, rate_func=linear)`.
- `always_redraw(lambda: Circle(radius=r.get_value(), ...))` for the balloon.
- Three `DecimalNumber` readouts for r, V=4/3πr³, and dr/dt = (dV/dt)/(4πr²).
- `dV/dt` is constant; show it as a `MathTex` label (not a readout).

**Run-time budget.** ~12s.

See `examples/pattern_10_related_rates.py`.

---

## Cross-cutting conventions

### Parameter sweep rate

Default: **1 data unit per second** when sweeping x along an axis. If a scene needs a faster sweep (e.g., quick overview), mark it explicitly in the narration. Sweeps over 5+ data units should be 5+ seconds.

### Axes coordinate discipline

All axes-anchored objects use `ax.to_point(x, y)` — no exceptions. Mixed scene/data coordinates cause objects to drift when axes are shifted or rescaled.

### Riemann rectangles

For height `f(xᵢ)`, compute the rectangle's world-unit height as `ax.to_point(xᵢ, f(xᵢ))[1] - ax.to_point(xᵢ, 0.0)[1]`. The rectangle anchors at `ax.to_point(xᵢ, 0.0)` and extends upward. Never compute world height directly from data height.

### always_redraw performance

Rebuild `always_redraw` factories should be cheap: one VMobject construction, reading a float from a tracker. Never call `plot_function` or `scipy.integrate` inside `always_redraw`. Pre-compute lookup tables before the animation starts.

---

## Gotchas / anti-patterns

- **Dividing by h when h approaches 0.** Drive to `0.01`, not `0.0`. Narration: "approaches zero".
- **Riemann rectangle heights in data units, not world units.** Use the world-unit delta from `ax.to_point`.
- **Calling `plot_function` inside `always_redraw`.** Builds 60 cubic segments 30×/second → slow render. Build the fixed graph once; only the moving elements use `always_redraw`.
- **Overloaded scenes.** Riemann bars + accumulator in one scene violates the `pedagogy-cognitive-load` rule. Split into two beats.
- **Adding target MathTex to scene before `TransformMatchingTex`.** Don't. chalk adds only the unmatched new glyphs automatically.
- **Flash mobjects not pre-added.** Call `self.add(m)` for each line in `flash.mobjects` before `self.play(flash)`.
- **`Transform` on two VGroups with different submobject counts.** Unpredictable morph. Use `FadeOut` old + `FadeIn` new instead.

---

## Changelog

- **0.1.0** (2026-04-21) — initial ship. Replaces `manim-calculus-patterns` per ADR 0001. Ten canonical calculus patterns ported to chalk's coordinate API (`ax.to_point` vs Manim's `ax.c2p`), animation API (`ChangeValue` vs `x.animate.set_value`, `FadeIn` vs `Create/DrawBorderThenFill`), and layout API (`place_in_zone`, `next_to`, `labeled_box`, `arrow_between`). Colour semantics aligned with chalk's design system (`color-and-typography`).
