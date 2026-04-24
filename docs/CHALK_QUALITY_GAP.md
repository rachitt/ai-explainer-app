# Chalk vs Manim — the quality gap and how to close it

**Load every session.** Referenced from `CLAUDE.md`. Every chalk-related PR must either close one of the gaps listed below or explain why it doesn't.

## Why this doc exists

Pedagogica replaced Manim Community Edition with in-repo chalk on 2026-04-21 (ADR 0001). The bet: repo-owned renderer evolves faster than an external framework. The cost: we give up eight years of compounded manim work. This doc is the honest accounting of what chalk lacks, why output quality lags, and the ordered plan to close the gap.

Kill criteria for reverting to manim live in `docs/adr/0001-chalk-replaces-manim.md` K1–K5. This doc is the plan to avoid triggering them.

## The gap — empirical, not hypothetical

| Dimension | Manim (CE) | Chalk today | Impact on output |
|---|---|---|---|
| Shape primitives | 40+ (NumberPlane, Matrix, BarChart, VectorField, ThreeDScene, Code, ArcBetweenPoints, CurvedArrow, AnnularSector, …) | 7 (Circle, Rectangle, Line, Arrow, Dot, Polygon, Path) | Agents reach for shapes that don't exist; fall back to `Rectangle + MathTex` composites that look hand-rolled. |
| Domain kits | Hundreds from the manim community | 5 (circuits, physics, chemistry, coding, graph) | Every non-core scene is hand-built, which is what we just saw on KVL. |
| Animation verbs | ~40 (DrawBorderThenFill, Wiggle, ApplyWave, GrowFromCenter, GrowArrow, ReplacementTransform, FadeTransform, ShowCreation, Uncreate, …) | ~15 (Write, Fade, Transform, ShiftAnim, Rotate, ChangeValue, MoveAlongPath, Indicate, Flash, Circumscribe, AnimationGroup, LaggedStart, Succession, plus our 5 composites) | Scenes feel monotone. Every reveal is a FadeIn; every transition is a Write. |
| MathTex | Variadic, glyph-indexable (`mobj[2]`), TransformMatchingTex mature | Single-string only, no indexed access, TransformMatchingTex had to be patched for `_new_mobs` | Any "highlight the x² in sin(x²)" scene needs four separate MathTex objects composed by hand. |
| Layout heuristics | 8 years of buff tuning baked into `next_to`, `arrange`, `get_corner` | `next_to` exists; buff is hand-picked per call | Preflight keeps catching overlaps that manim would auto-avoid. |
| Camera | `MovingCameraScene`, pan/zoom tracks with easing | `CameraShift`, `CameraZoom` — basic | No smooth object-tracking, no picture-in-picture, no scene composition. |
| Axes presets | `NumberPlane`, `ComplexPlane`, `ThreeDAxes`, `PolarPlane` | `Axes` only (manual range/width) | Every graph starts from scratch. |
| Rendering backend | OpenGL + cached shaders, 60fps, antialiased | cairo rasterizer, 30fps | Noticeable on motion. |
| Example corpus LLMs have trained on | 3Blue1Brown source + thousands of community repos | ~20 scenes, all ours, not on the internet | LLMs pattern-match examples more than rules. No examples = no taste. |

**The eighth row is the single biggest lever.** Even if we match every other row, an LLM writing chalk has nothing to imitate. Manim output quality comes mostly from the corpus the model has seen.

## Why shipping gates alone doesn't close the gap

Gates (under_duration, cadence validators, depth-budget, hook-question propagation, derivation-chain, strict preflight) are REJECTION machinery. They catch bad output and trigger a retry. They do not teach agents what good output is.

Closing the gap requires GENERATION improvement:
1. Richer primitives — agents cannot reach for tools that don't exist.
2. More reference scenes — agents imitate; give them models to imitate.
3. Better layout heuristics — fewer preflight retries.
4. MathTex parity — allows surgical highlighting of sub-expressions.

Gates remain valuable as safety nets, but the next 6–8 weeks of work should be heavily tilted toward generation.

## Prioritised backlog

Ordered by expected impact × tractability. Each item has a target PR size and an acceptance signal (what must be true for the gap row to count as closed).

### P0 — Reference corpus (highest impact)

Agents copy examples. Corpus size × quality caps output quality. Hand-author canonical scenes until each domain has 5+ rendered, reviewed, SKILL-catalogued examples.

- **P0.1 Calculus corpus.** Already 10 patterns catalogued, 2 restated with composites. Target: 10/10 using composites, each rendered to mp4 and reviewed.
- **P0.2 Circuits corpus.** 2 patterns (RC loop, KVL walker). Target: +3 (RL series, voltage divider, node analysis) using the new `KirchhoffDemo` physics mode.
- **P0.3 Physics corpus.** 3 templates (projectile, pendulum, spring-mass) + 1 canonical. Target: +2 (free-body with solve, energy bar chart).
- **P0.4 Chemistry corpus.** Minimal today. Target: 3 canonical (reaction-mechanism, bond rotation, orbital hybridisation).
- **P0.5 Graph / coding corpora.** Minimal today. Target: 3 each.

**Acceptance:** every `chalk-*-patterns` SKILL lists ≥5 canonical examples with usage + `pattern_NN_*.py` file + rendered reference mp4.

### P1 — Animation verb expansion

Port the missing 10–15 high-use manim animations. Each is one class + unit test + export + SKILL catalog entry.

- `DrawBorderThenFill` (outlines a shape then fills — the signature 3B1B reveal)
- `GrowFromCenter`, `GrowArrow`
- `ShowCreation` / `Uncreate` (inverse Write)
- `ReplacementTransform`, `FadeTransform`
- `Wiggle` (shake-to-attention)
- `ApplyWave` (sinusoidal distortion)
- `CyclicReplace`
- `Swap`
- `MoveToTarget`

**Acceptance:** `chalk-primitives` SKILL "Animation" section covers ≥25 verbs. Each has a one-liner usage example.

### P2 — MathTex parity with manim

Today's single-string limit is the reason every sub-expression highlight has to be hand-composed.

- P2.1 Variadic signature: `MathTex(*tex_strings, color=..., scale=...)` — renders each string as a separate child VMobject, positioned by LaTeX spacing.
- P2.2 Indexed access: `expr[0]`, `expr[1]`, … returns children so `Circumscribe(expr[2])` works.
- P2.3 `TransformMatchingTex` hardening — cover the edge cases that tripped us in `workflows/lessons.md` (unmatched target glyphs, nested VGroups).

**Acceptance:** `Circumscribe(MathTex(r"\sin", r"(", r"x^2", r")")[2])` lights up just `x^2` in a rendered scene. SKILL documents the pattern.

### P3 — Composite primitive expansion

Build on the 5 composites (`reveal_then_explain`, `highlight_and_hold`, `annotated_trace`, `animated_wait_with_pulse`, `build_up_sequence`). Add:

- `equation_buildup(terms)` — renders `a + b + c = d` one term at a time with inter-term spacing preserved.
- `derivation_chain(steps)` — each step morphs into the next via TransformMatchingTex.
- `callout(target, text, direction)` — arrow + label + bracket in one call.
- `grid_of(items, rows, cols, spacing)` — 2D arrangement helper.
- `timeline(events, duration)` — horizontal bar with tick marks + event labels.
- `progress_gauge(value_tracker, max_value)` — live arc fill.

**Acceptance:** `chalk-primitives` SKILL lists 10+ composites; each appears in ≥1 canonical pattern.

### P4 — Layout heuristic maturation

Port manim's `arrange`, `arrange_in_grid`, proper `next_to` with automatic `buff` selection by scale tier, `align_to`, `get_corner`.

- P4.1 `arrange(mobjects, direction, buff)` — lays out a list along a direction.
- P4.2 `arrange_in_grid(mobjects, rows, cols, buff)` — 2D grid.
- P4.3 `next_to(..., buff=None)` with auto-buff: picks `0.15` for `SCALE_ANNOT`, `0.25` for `SCALE_LABEL`, `0.35` for `SCALE_BODY`, `0.45` for `SCALE_DISPLAY`. Dramatically fewer manual buff tweaks.
- P4.4 `align_to(target, reference, edge)`.

**Acceptance:** preflight-overlap PR rate drops. `chalk-lint` R5 / R9 trigger less often in real scenes (measured on the regression test suite).

### P5 — Axes presets

Three additions:

- `NumberLine(start, end, tick_interval, label_tiers)`.
- `NumberPlane(x_range, y_range, grid_subdivisions)`.
- `Axes.preset(kind)` with kinds `"symmetric_unit"` (–1..1 both axes), `"zero_to_one"`, `"wide_shallow"`, `"calculus_default"` (0..2π x, –1..1 y).

**Acceptance:** chalk-calculus-patterns scenes drop the raw `Axes(x_range=(0, 4), y_range=(0, 6), width=8, height=5)` lines in favour of `Axes.preset("calculus_default")`.

### P6 — Rendering backend polish (lowest priority, high effort)

OpenGL path is out of scope for this phase. In-scope cairo polish:

- Antialias stroke endpoints (currently visible on resistor zigzags).
- 60fps option (today fixed at 30).
- Higher-res MathTex cache (current rasterisation shows on macOS Retina).

**Acceptance:** A/B comparison of a chalk render against a manim render at 1080p is indistinguishable for a calculus-depth scene. Optional, track but do not block other P-items on this.

## Cadence

- One P0 corpus PR per week, rotating domains.
- One P1 verb PR per week (bundle 3–4 verbs).
- P2 MathTex work as a single focused PR, probably 1–2 weeks.
- P3 composites as drops of 2–3 per PR, after the P0 scenes demand them.
- P4 layout heuristics piggy-backed on P0 corpus PRs when the needed helper is missing.
- P5 axes presets when P0.1 (calculus corpus) lands.

## Session-start checklist

Every session that touches chalk or agent scenes:

1. Read `workflows/lessons.md` (mandatory, per `CLAUDE.md` line 1).
2. Read this file (`docs/CHALK_QUALITY_GAP.md`).
3. Identify which P-item the proposed work closes. If none, justify.
4. Prefer lifting primitives / examples over patching individual scenes.

## Measuring progress

Track in `docs/CHALK_QUALITY_GAP_STATUS.md` (to be created as the backlog burns down):

- Primitive count (target: match manim's 40 core shape primitives).
- Animation verb count (target: 25+).
- Canonical examples per domain (target: 5 per `chalk-*-patterns` SKILL).
- Preflight-overlap rate on regression scenes (target: decline over time).
- Average chalk-repair attempts per scene (target: ≤1.2).

Don't let a session end without some line on this dashboard moving.
