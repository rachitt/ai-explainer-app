---
name: manim-calculus-patterns
version: 0.1.0
category: manim
triggers:
  - domain:calculus
  - stage:visual-planner
  - stage:manim-code
  - stage:manim-repair
requires:
  - scene-spec-schema@^0.1.0
  - manim-primitives@^0.1.0
  - latex-for-video@^0.1.0
  - color-and-typography@^0.1.0
token_estimate: 6800
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Ten canonical Manim patterns for calculus explainer scenes — derivative as
  slope, moving tangent tracker, left/midpoint Riemann sums, the Riemann →
  integral limit, ε-δ limit window, chain-rule composition, FTC area
  accumulator, function shift/scale transformations, product rule as a box,
  and related rates. Each pattern is a runnable scene plus a note on which
  SceneBeat shapes it serves. Loaded by the visual planner when the scene
  belongs to a calculus beat and by the Manim-code agent on every calculus
  codegen.
---

# manim-calculus-patterns

## Purpose

Undergraduate calculus has ten-odd visual moves that keep showing up: a tangent line that follows a point along a curve, a stack of rectangles approximating an area, a ball rising and falling, a ε-ball shrinking around a limit. 3Blue1Brown, Khan Academy, and most good textbook figures reuse these moves; so should we.

This skill catalogues the ten patterns as Manim scenes. Each is written so the visual planner can read the scene structure and the Manim-code agent can adapt it — substituting the specific function, interval, or parameters the current topic calls for. The patterns are not templates (no string substitution); they're worked examples the agent learns from by reading, then re-derives in its output.

Every example in `examples/` runs with `manim -ql` and produces an MP4. Several require LaTeX (see `manim-debugging` entry `latex-missing-package`); the file-level docstring flags each one.

## When to load

- **Visual planner — when `scene_beat.domain == calculus`**. Consult to pick which pattern to stage and generate concrete `animation_plan` entries accordingly.
- **Manim-code agent — always for calculus scenes.** The pattern examples carry the run-time budgets, the `c2p` usage, and the updater idioms the agent needs.
- **Manim-repair — on retry.** Repair often means "this should have been pattern X". The pattern pack is loaded to give the agent a reference it can compare the failing code against.
- **Not needed by:** storyboard, script, script-critic, TTS, editor, subtitle.

## Pattern index

| # | Pattern | Example file | Typical beat type | Requires LaTeX |
|---|---|---|---|---|
| 01 | Derivative as slope (secant → tangent) | `pattern_01_derivative_as_slope.py` | `define`, `hook` | yes |
| 02 | Tangent line tracker | `pattern_02_tangent_tracker.py` | `example`, `generalize` | no |
| 03 | Left-Riemann sum | `pattern_03_riemann_left.py` | `example` | no |
| 04 | Riemann → integral limit | `pattern_04_riemann_to_integral.py` | `generalize` | no |
| 05 | ε-δ limit window | `pattern_05_epsilon_delta.py` | `define`, `motivate` | yes |
| 06 | Chain rule composition (nested boxes) | `pattern_06_chain_rule_boxes.py` | `example` | yes |
| 07 | FTC area accumulator | `pattern_07_ftc_accumulator.py` | `example`, `generalize` | no |
| 08 | Function transformation (shift / scale) | `pattern_08_function_transformation.py` | `example` | no |
| 09 | Product rule as a box | `pattern_09_product_rule_box.py` | `example` | no |
| 10 | Related rates (balloon inflating) | `pattern_10_related_rates_balloon.py` | `example` | no |

Pattern files are self-contained Scene subclasses. Class names are the pattern name in PascalCase (e.g., `DerivativeAsSlope`).

## Pattern 01 — Derivative as slope (secant → tangent)

**Idea.** Draw the curve. Place two points on it, connect them with a secant line, display the slope as rise/run. Slide the second point toward the first; the secant rotates and the slope readout updates. When the two points coincide, the secant has become the tangent and the readout is the derivative.

**Beats this serves.** `define` ("what is a derivative"), `hook` (classic opening).

**Key mechanics.**
- Two `ValueTracker`s (or one parameter `h` with fixed anchor) for the two points.
- `always_redraw` on the secant line, the rise-run brackets, and the slope readout — all read the same trackers.
- Drive `h → 0` with `self.play(h.animate.set_value(0.01), run_time=3.0)`. Don't go to exactly 0 (the slope formula divides by h); go to a small positive value.

**Run-time budget.** ~12–14s end-to-end (curve draw 2s, points place 1s, secant create 1s, sweep 3s, tangent label 1.5s, beat on the result 1.5s).

See `examples/pattern_01_derivative_as_slope.py`.

## Pattern 02 — Tangent line tracker

**Idea.** Fix a curve. A tangent line and a dot move continuously along the curve, parameterized by one `ValueTracker` on x. A slope readout updates in sync.

**Beats this serves.** `example` (evaluate derivative at specific points), `generalize` (derivative as a function).

**Key mechanics.**
- One `ValueTracker(x0)`, parameter on x.
- `always_redraw(lambda: Dot(ax.c2p(x.get_value(), f(x.get_value()))))`
- Tangent line built as a short `Line` centred on the dot with slope `f'(x)`, half-length ~1 unit. Rebuild it each frame via `.add_updater` + `.become(new_line)` (not `always_redraw` — allocating a new Line every frame is expensive).
- Slope readout: a `MathTex` below the curve whose substring index for the number gets replaced each frame. Or a Text with f-string formatting for the no-LaTeX path (see example).

**Run-time budget.** Drive sweeps at ~1 x-unit per second (e.g., x=−1 → x=3 over 4s).

See `examples/pattern_02_tangent_tracker.py`.

## Pattern 03 — Left-Riemann sum

**Idea.** Under a curve, draw N left-endpoint rectangles. Their total area is the left-Riemann approximation. Label the sum ΣᵢᴺᴵL f(xᵢ)Δx.

**Beats this serves.** `example` (concrete approximation of an integral).

**Key mechanics.**
- `Rectangle` per subinterval. Width = (b−a)/N; height = f(xᵢ); anchor at `ax.c2p(xᵢ, 0)` with `next_to(..., UP, buff=0)` giving the right top.
- Iterate with `[Rectangle(...) for i in range(N)]`, put into a `VGroup`, `DrawBorderThenFill` over the group with `lag_ratio=0.05` so they cascade.
- For Phase 1, N = 8 is a sweet spot (visible rectangles, clearly approximating).

**Run-time budget.** Curve draw 2s, rectangles cascade 2s (0.25s × 8), label beat 1s.

See `examples/pattern_03_riemann_left.py`.

## Pattern 04 — Riemann → integral limit

**Idea.** Start with a crude (N=4) Riemann approximation; animate the rectangles getting narrower and more numerous until they visually fuse into the smooth area under the curve. Label transitions Σ → ∫.

**Beats this serves.** `generalize` (definition of the integral via limit).

**Key mechanics.**
- One `ValueTracker(N)` if you want continuous N, but stepped `N ∈ {4, 8, 16, 32, 64}` reads more clearly. For each step, `ReplacementTransform` the old rectangles VGroup into the new one.
- At the final step, `ReplacementTransform` the VGroup into a filled `Polygon` representing the exact area under the curve.
- LaTeX label: `MathTex(r"\sum", ...)` morphs into `MathTex(r"\int", ...)` via `TransformMatchingTex`. Use `latex-for-video` patterns for the indexed substrings.

**Run-time budget.** 12–14s: four N-steps at 1.5s each plus final morph 2s plus labels 3s.

See `examples/pattern_04_riemann_to_integral.py`.

## Pattern 05 — ε-δ limit window

**Idea.** Show a function with a designated limit point `a` on the x-axis and limit value `L` on the y-axis. Draw a horizontal band of half-width ε around L ("output window") and a vertical band of half-width δ around a ("input window"). Shrink ε; the required δ shrinks in response. The visual argument: for every ε, we can find a δ.

**Beats this serves.** `define`, `motivate` (why limits have this shape).

**Key mechanics.**
- Two `ValueTracker`s (ε, δ) linked via an explicit relationship for the example function (e.g., δ = ε/|slope| for a linear f, δ = √ε for f(x)=x²).
- `always_redraw` on two rectangles (ε-band, δ-band).
- `always_redraw` on highlighted portion of the curve where x is in δ-band; check visually that its vertical extent lies within ε-band.
- Drive ε from 1.0 → 0.2 over 4s. δ follows automatically.

**Run-time budget.** 14–18s total: setup 4s, shrink 4s, second shrink 4s, beat 3s.

See `examples/pattern_05_epsilon_delta.py`.

## Pattern 06 — Chain rule composition (nested boxes)

**Idea.** Represent f(g(x)) as two nested boxes: x enters the inner box labelled `g`, outputs `g(x)`, which enters the outer box labelled `f`, outputs `f(g(x))`. Then the derivative: a small perturbation dx enters, produces dg = g'(x)dx, which produces df = f'(g(x))·dg = f'(g(x))·g'(x)·dx.

**Beats this serves.** `example` (chain-rule intuition).

**Key mechanics.**
- Two `Rectangle`s (inner and outer) grouped.
- Three labels: `x`, `g(x)`, `f(g(x))` — all `MathTex`.
- Arrows via `Arrow(start_point, end_point)`, labelled with the local derivative.
- Use `TransformMatchingTex` to morph the output label from `f(g(x))` to `f'(g(x))·g'(x)·dx` when the derivative beat begins.

**Run-time budget.** 10–12s.

See `examples/pattern_06_chain_rule_boxes.py`.

## Pattern 07 — FTC area accumulator

**Idea.** A curve y = f(t) on the t-axis. A moving vertical line at `t = x` slides from `a` rightward; as it slides, a shaded region between `a` and `x` grows, and its numeric area A(x) is plotted on a second pair of axes below (or right). The visual statement: A'(x) = f(x).

**Beats this serves.** `example`, `generalize`.

**Key mechanics.**
- One `ValueTracker(x)` driving everything.
- `always_redraw` on the vertical line (a short `Line`), the shaded region (`ax.get_area(graph, x_range=[a, x])`), and the dot on the accumulator axes.
- Accumulator axes use a second Axes placed below via `next_to`. Its graph is built with `plot(lambda x: integral_numerical(f, a, x))` — for Phase 1, a pre-computed scipy integral or an antiderivative expression.
- Drive x from `a` to `b` over 4–5s.

**Run-time budget.** 14–16s.

See `examples/pattern_07_ftc_accumulator.py`.

## Pattern 08 — Function transformation (shift / scale)

**Idea.** Start with `y = f(x)`. Morph it to `y = f(x) + c` (vertical shift), then `y = f(x − h)` (horizontal shift), then `y = a·f(x)` (vertical scale), then `y = f(b·x)` (horizontal scale). Each morph is a `Transform` on the graph while keeping the axes fixed.

**Beats this serves.** `example` (graphical effects of parameter changes).

**Key mechanics.**
- Axes fixed; graph is the thing that transforms.
- Each new graph: `ax.plot(transformed_function)`.
- `Transform(old_graph, new_graph)` — or `ReplacementTransform` if the reference will be reused.
- Label each transformation with a `Text` or `MathTex` that morphs alongside.

**Run-time budget.** 4 transformations × 1.5s each plus holds = ~12s.

See `examples/pattern_08_function_transformation.py`.

## Pattern 09 — Product rule as a box

**Idea.** Draw a rectangle with side lengths `u` and `v`, so its area is `uv`. Extend the rectangle slightly: u becomes u+du, v becomes v+dv. The new area = old area + strip of width `du` on one side + strip of width `dv` on the other + tiny du·dv corner (shown shrinking to nothing). Therefore d(uv) = v·du + u·dv.

**Beats this serves.** `example` (visual proof of the product rule).

**Key mechanics.**
- Main rectangle at `(−2, −1.5)` to `(1, 1.5)` initially, so sides are clearly labelled.
- Three rectangles for the three "new" pieces in different colours, animated in with `FadeIn` after the main box grows.
- Labels `u`, `v`, `du`, `dv`, `v du`, `u dv`, `du dv` placed next to their respective edges/regions.
- At end, fade the tiny `du dv` corner and rewrite the growth sum as `d(uv) = v du + u dv`.

**Run-time budget.** 12–14s.

See `examples/pattern_09_product_rule_box.py`.

## Pattern 10 — Related rates (balloon inflating)

**Idea.** A sphere (shown as a circle) inflates at a constant volumetric rate `dV/dt`. The radius grows at a non-constant rate `dr/dt = (dV/dt) / (4πr²)`. Show the circle growing, with numeric readouts of V, r, dV/dt (constant), and dr/dt (decreasing).

**Beats this serves.** `example`.

**Key mechanics.**
- One `ValueTracker(r)` plus explicit closed-form `V(r) = (4/3)πr³`.
- `always_redraw` on the circle with radius `r.get_value()`.
- Readouts built via `Text` + f-string (no LaTeX path) or `MathTex` with TransformMatchingTex each timestep.
- Drive `r` from 0.5 to 2.0 over 5s. Compute `dr/dt = dV/dt / (4π r²)` in the narration; the visual shows it slowing.

**Run-time budget.** 10–12s.

See `examples/pattern_10_related_rates_balloon.py`.

## Cross-cutting conventions

### Rate of parameter change

The tracker-driven patterns all follow the same convention: **1 x-unit per second** is the default sweep rate. If a scene needs faster (e.g., a quick sweep to show range), mark it explicitly with a run_time override and note in the narration ("quickly, watch this sweep").

### Colour semantics

- Curve: `BLUE`.
- Tangent / slope indicator: `RED`.
- Area / integral region: `GREEN` with `fill_opacity=0.5`.
- Secondary curve (comparison): `YELLOW`.
- Annotations / underbraces: `WHITE`.
- Axes: `GRAY`.

See `color-and-typography` for the full palette. These are the calculus-specific defaults.

### Axes scale

For most calculus scenes, a 7×4 unit axes (`x_length=7, y_length=4`) at centre leaves room above for a TOP label and below for a BOTTOM readout — see `scene-composition` §5.1.

### LaTeX in readouts

MathTex readouts that change every frame (e.g., slope = 3.45) need `TransformMatchingTex` on the changed substring, not a `Write` from scratch each frame. The LaTeX compile is cached for identical substrings but flickers visibly if you `add/remove` instead of `transform`.

For the no-LaTeX path (local dev without tlmgr install), use `always_redraw(lambda: Text(f"slope = {m.get_value():.2f}"))`. Ship the LaTeX version in production; develop on the Text version.

## Gotchas / anti-patterns

- **Crude Riemann rectangles that clip the curve.** The rectangle heights read wrong if the curve dips below them. For left-Riemann, the rectangle top is `f(xᵢ)`; for a decreasing function this is above the curve on the right side of the bar and looks like an overestimate (it is). Don't accidentally anchor rectangles to `f(xᵢ₊₁)` — that's right-Riemann.
- **Dividing by h in a secant slope when h=0.** Drive h to `0.01`, not `0`. Narration can say "approaches zero".
- **Updaters left attached through the scene's final wait.** Especially tangent trackers: you see a phantom jitter on the last frame. Always `.clear_updaters()` before the final `self.wait`.
- **Mixing scene coords and data coords.** `Dot([2, 4, 0])` is a scene-coord placement that won't follow axis rescaling; `Dot(ax.c2p(2, 4))` is. Use `c2p` on any Axes-anchored object.
- **Computing numeric antiderivatives every frame.** In pattern 07, if you re-integrate scipy each frame you'll render at 0.5 fps. Precompute `A(x)` as an ax.plot on the accumulator axes before the animation starts.
- **Overloaded scenes.** A single scene trying to do both pattern 03 (Riemann bars) and pattern 07 (accumulator) at once fails the `pedagogy-cognitive-load` rest-frame rule. Split into two scenes.
- **Using `Transform` on a graph while the underlying `Axes` changes.** Both mobjects must share a coordinate system for the morph to read. Either fix the axes or group them.
- **Pattern drift.** Modifying a pattern to fit a specific scene is fine; modifying a pattern in this skill to match a specific scene's needs is not. If you find yourself wanting to edit `pattern_05_epsilon_delta.py` because a particular ε-δ scene didn't read, fix the scene's code, not the pattern.

## Examples

See each `pattern_NN_…py` under `examples/`. Class names (for `manim` CLI):

- `DerivativeAsSlope` · `TangentTracker` · `RiemannLeft` · `RiemannToIntegral`
- `EpsilonDelta` · `ChainRuleBoxes` · `FTCAccumulator` · `FunctionTransformation`
- `ProductRuleBox` · `RelatedRatesBalloon`

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. 10 canonical patterns covering derivative definition, moving tangent, Riemann sums (left + limit), ε-δ, chain rule, FTC, graph transformations, product rule, related rates. Cross-cutting conventions for parameter rates, colour semantics, axes sizing, and the LaTeX / Text dev-mode trade-off. Paired with `manim-primitives`, `latex-for-video`, and `color-and-typography`.
