---
name: domain-calculus
version: 0.1.0
category: domain
triggers:
  - domain:calculus
requires: []
token_estimate: 3800
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Phase-1 calculus domain pack: curriculum map (20 canonical topics in five
  groups), per-topic motivating example and preferred notation, common student
  misconceptions, and prerequisite dependencies. Loaded by the curriculum and
  storyboard agents to pick scenes; referenced by the script agent for
  terminology. The only domain pack in Phase 1.
---

# domain-calculus

## Purpose

A domain pack is the answer to "what does the agent need to know about this subject that isn't in the pedagogy skills?" For calculus, that's: which topics form the canonical curriculum, what the motivating example for each is, which notation is preferred, and which misconceptions the narration should defuse. This skill is the lookup table the curriculum agent reads when turning a user prompt ("explain the chain rule") into a curriculum plan, and the script agent reaches for when deciding between `dy/dx` and `f'(x)`.

Pedagogy skills (`pedagogy-sequencing`, `explanation-patterns`, `pedagogy-cognitive-load`) tell the agent *how* to teach; this pack tells it *what* to teach.

## When to load

- Curriculum agent — **always** in Phase 1 (every job is calculus).
- Storyboard agent — **conditional**; load when picking scene beats benefits from topic-specific canonical examples.
- Script agent — **conditional**; load when the scene's terminology or notation needs a domain-preferred form.
- Pedagogical critic — **conditional** on the critic checking factual content; Phase 1 critics are report-only so the load is optional.
- Do not load for visual/audio tiers — they're domain-agnostic.

## Core content

### Curriculum map (20 canonical topics, five groups)

Topics are listed in roughly increasing sophistication within each group. The 10 bolded topics are the Phase-1 regression set (`docs/ROADMAP.md` §3 Week 6).

#### Group 1 — Limits and continuity

1. **Intuitive limit** — limits described as "the value a function approaches." The scene-worthy anchor for the rest of the course.
2. Epsilon–delta limit — the formal `∀ε > 0 ∃δ > 0 …` version. Motivate by showing that "approaches" needs a precise meaning for mathematicians to agree.
3. **Limits (ε–δ, concrete example)** — the ε–δ formalism applied to a specific limit (e.g. `lim_{x→2} (3x+1) = 7`). Phase-1 regression target.
4. One-sided limits — the left and right limits, with the standard compare/contrast pattern (see `explanation-patterns`).
5. Continuity — a function is continuous at `a` when the three-way agreement holds: `f(a)` exists, the limit exists, and they match.

#### Group 2 — Derivatives

6. **Derivative as rate of change** — the "instantaneous speed" motivation. Anchor: position vs. time with speedometer analogy.
7. **Derivative as slope of tangent** — the geometric motivation. Anchor: `y = x²`, secant sliding to tangent.
8. **Product rule (visual proof)** — the area-of-a-rectangle-with-expanding-sides argument. Avoid the purely algebraic derivation; it doesn't land.
9. **Chain rule (intuition)** — the "nested speeds" picture, or the stacked-gears analogy. Formal statement is the generalize slot of a DMEG beat.
10. Implicit differentiation — for `x² + y² = 1`, differentiate both sides as identities in `x`. Motivate by "what if `y` isn't isolated?"
11. **Related rates (balloon inflating)** — the classical motivation. Volume relating to radius; given `dr/dt`, compute `dV/dt`. Phase-1 regression target.

#### Group 3 — Applications of derivatives

12. **Optimization (box with max volume)** — the paper-with-corners-cut-out classic. Maximising `V(x) = x(a−2x)²`. Phase-1 regression target.
13. Newton's method — `x_{n+1} = x_n − f(x_n)/f'(x_n)`. Visual: tangent line slope intersects x-axis. Optional in Phase 1.
14. Linearisation — `f(x) ≈ f(a) + f'(a)(x − a)` for `x` near `a`. Motivate with "estimate `√4.1`."

#### Group 4 — Integrals

15. **Riemann sum → integral** — rectangles approximating area under `y = f(x)`; shrinking widths; the limit is the definite integral. Phase-1 regression target.
16. **Fundamental theorem of calculus (part 1)** — `d/dx ∫_a^x f(t) dt = f(x)`. Visual: sweeping bar; area grows at the rate of the bar's height. Phase-1 regression target.
17. Substitution — `u = g(x)`, `du = g'(x) dx`. Motivate as chain-rule reversed.
18. **Area between curves** — two functions, integrate the difference. Phase-1 regression target.

#### Group 5 — Series (Phase-1 optional)

19. Sequences and their limits — a gentle on-ramp to infinite processes.
20. Convergence tests / Taylor series — polynomial approximations of transcendental functions. Visual: a polynomial of growing degree hugging `sin(x)` more and more tightly.

Total: 20 topics. Phase-1 videos are 2–4 min, single-topic each. A topic occupies the whole video; the storyboard splits it into 5–8 beats.

### Per-topic canonical material

For each of the 10 Phase-1 regression topics: anchor example, preferred notation, common misconception, one-line visual intent.

#### 1. Intuitive limit

- **Anchor**: `lim_{x→2} (x² − 4)/(x − 2)`. Indeterminate at `x = 2`; factorable; limit = 4.
- **Notation**: `lim_{x→a} f(x)` in prose; avoid `x → a` alone without `lim`.
- **Misconception**: "the limit is the value at the point." Defuse: it's about what the function *approaches* as `x` moves toward `a`, not about `f(a)`. The example above is designed to make this inescapable.
- **Visual intent**: a curve with a hollow point at `x = 2`; the y-value slides up to 4 as x approaches from either side.

#### 2. Limits (ε–δ, concrete)

- **Anchor**: `lim_{x→2} (3x + 1) = 7`. Show that given any `ε > 0`, choosing `δ = ε/3` works.
- **Notation**: the full `|x − a| < δ ⇒ |f(x) − L| < ε`. Don't abbreviate; the pedagogy is in the structure.
- **Misconception**: "δ has to be small." Defuse: δ just has to work; often the trickiness is that small ε forces small δ, not the reverse.
- **Visual intent**: an ε-band around `L` on the y-axis; a δ-band around `a` on the x-axis; shrinking ε forces shrinking δ, shown live.

#### 3. Derivative as rate of change

- **Anchor**: position function `s(t) = t²`. Speedometer at `t = 1` reads `s'(1) = 2`.
- **Notation**: `ds/dt` in prose (rate-of-change flavour); `s'(t)` fine as shorthand once introduced.
- **Misconception**: "instantaneous speed is just average speed over a very tiny interval." Defuse: explicitly call out that no *actual* interval works; the limit of shrinking intervals is the new object.
- **Visual intent**: a speedometer widget updating as a dot moves along `s(t) = t²`; needle and slope synchronised.

#### 4. Derivative as slope of tangent

- **Anchor**: `y = x²`. Secant between `(1, 1)` and `(1+h, (1+h)²)` rotates toward tangent as `h → 0`; slope approaches `2`.
- **Notation**: `f'(x)` preferred for "the derivative as a function"; `f'(a)` for "derivative at a point."
- **Misconception**: "the tangent touches the curve at exactly one point." Defuse: counterexamples (tangent to `y = x³` at origin crosses the curve). The tangent is the linear *approximation*, not a one-touch visual.
- **Visual intent**: two points on a parabola slide toward each other; secant line rotates and settles into the tangent.

#### 5. Chain rule (intuition)

- **Anchor**: `f(g(x))` with `g(x) = 3x` and `f(u) = u²`. Show that when `x` moves by `Δx`, `g` moves by `3Δx`, and `f` moves by `2u · 3Δx`. Ratio: `6u`.
- **Notation**: Leibniz `dy/dx = dy/du · du/dx` lands the intuition best ("rates multiply"). Prime notation `(f∘g)'(x) = f'(g(x)) · g'(x)` for the generalise slot.
- **Misconception**: "you only differentiate the outer function." Defuse: the whole *point* is that the inner rate is also part of the answer. Prime-notation symbols hide this; Leibniz makes it visible.
- **Visual intent**: stacked gears of different sizes; one full turn of the outer gear requires the inner gear to turn faster.

#### 6. Product rule (visual proof)

- **Anchor**: `f(x) · g(x)` as the area of a rectangle with sides `f(x)` and `g(x)`. When both grow, the new area comes from two rectangular strips (one on each side), plus a negligible corner.
- **Notation**: `(fg)' = f'g + fg'`. State it after the picture lands.
- **Misconception**: "the derivative of a product is the product of the derivatives." The very error the rule exists to correct. Defuse by setting up the compare/contrast directly.
- **Visual intent**: a rectangle with both dimensions pulsing; the two new side-strips light up as the two summands of the rule.

#### 7. Riemann sum → integral

- **Anchor**: `∫_0^2 x² dx`. Four rectangles first (crude), then 8, then 16; the approximation improves.
- **Notation**: `∫_a^b f(x) dx` with a thin space before `dx`: `\int_a^b f(x)\,dx`.
- **Misconception**: "the integral is the anti-derivative." (That's the FTC conclusion, not the definition.) Defuse: the integral is *defined* as a limit of sums; the anti-derivative is a computational shortcut the FTC provides.
- **Visual intent**: a thin bar sweeps under the curve; rectangle count doubles; error strip shrinks.

#### 8. Fundamental theorem of calculus (part 1)

- **Anchor**: `A(x) = ∫_0^x f(t) dt` where `f(t) = t`. Show that `A(x) = x²/2`, so `A'(x) = x = f(x)`.
- **Notation**: `d/dx ∫_a^x f(t) dt = f(x)`. Mind the dummy variable (`t`); never reuse `x` inside and outside.
- **Misconception**: "FTC says the integral equals the derivative." It says they're *inverse* operations, applied in the right order to the right objects. Defuse by showing the chain of three objects: `f`, its running-area `A`, and `A`'s rate of change.
- **Visual intent**: a sweeping vertical bar fills area leftward-to-rightward; a second panel plots the running area `A(x)`; the slope of `A` at each `x` equals the height `f(x)`.

#### 9. Related rates (balloon inflating)

- **Anchor**: spherical balloon, `V = (4/3)πr³`. Given `dV/dt = 100 cm³/s`, find `dr/dt` when `r = 5 cm`.
- **Notation**: chain-rule flavour. `dV/dt = dV/dr · dr/dt`; solve for `dr/dt`.
- **Misconception**: "plug in `r = 5` before differentiating." Defuse by insisting on the order: differentiate the relationship as an identity in `t`, *then* substitute the given instant.
- **Visual intent**: an inflating sphere (or circle in 2D), with `V` and `r` both updating; two sliders, visually tying one rate to the other.

#### 10. Optimization (box with max volume)

- **Anchor**: flat square of side `a = 12`, cut corners of side `x`, fold up. `V(x) = x(12 − 2x)²`. Maximise by finding `V'(x) = 0`.
- **Notation**: `V'(x)` clean here; no Leibniz needed.
- **Misconception**: "endpoints don't matter." Defuse: the domain `[0, 6]` bounds matter; check them against the critical point.
- **Visual intent**: a flat square with corner-squares cut out, animated folding up into a box; a plot of `V(x)` next to it with a moving dot; the dot reaches the peak.

### Notation conventions (across topics)

- **Derivatives in prose**: `dy/dx` when the flavour is "rate of change" (physics-like); `f'(x)` when the flavour is "a new function." Pick one per video.
- **Chain rule**: prefer Leibniz when the intuition is multiplicative rates; switch to prime notation for the generalise slot.
- **Integrals**: always `\int f(x)\,dx` with a thin space. In narration: "the integral of `f(x)` with respect to `x`."
- **Limits**: `\lim_{x \to a}` with `x \to a` under the `\lim`, not inline. Say "the limit as `x` approaches `a`."
- **Dummy variables**: when a bound variable (dummy) appears in an integral or sum, give it a distinct letter from anything free in the outer context. `∫_0^x f(t) dt`, not `∫_0^x f(x) dx`.
- **Evaluation bars**: `[F(x)]_a^b` or `F(b) − F(a)` — pick one per video.

### Prerequisite graph (which topics assume what)

- **Limits** (group 1) assume functions, graphs, algebra. No prereqs from this pack.
- **Derivatives** (group 2) assume Group 1 (at least intuitive limits).
- **Applications of derivatives** (group 3) assume Group 2.
- **Integrals** (group 4) assume Group 2 (derivatives are inputs to FTC). Riemann sum itself only assumes limits.
- **Series** (group 5) assume Group 4.

Phase-1 regression prompts are phrased to be self-contained (e.g. "explain chain rule" assumes derivative has been introduced within the same video). Users requesting topics without clear prerequisites get a curriculum that builds them in — the curriculum agent's job, guided by `pedagogy-sequencing`'s "backwards from the goal."

## Examples

### Example 1 — curriculum expansion from user prompt

Prompt: "explain the chain rule."

Expanded curriculum (curriculum agent, this pack loaded):
- LO1: derivative as rate of change (prereq, short).
- LO2: chain rule intuition via stacked gears.
- LO3: chain rule formula, applied to `(3x)²`.
- Misconceptions to preempt: "only differentiate the outer." Explicit in LO2.
- Anchor: `g(x) = 3x`, `f(u) = u²`, `(f∘g)(x) = 9x²`.

### Example 2 — notation choice

Script draft (beat 3): "Now we take the derivative of `f(g(x))`. Using Leibniz notation, `dy/dx = dy/du · du/dx` — the rates multiply."

Why Leibniz here: the rate-of-change flavour is load-bearing; `(f∘g)'(x) = f'(g(x)) · g'(x)` works but obscures the multiplicative intuition.

### Example 3 — misconception defusion

Topic: Riemann sum. The anchor shows rectangles under `y = x²` on `[0, 2]`. Before concluding, the narration explicitly says: "this is the *definition* of the integral — as a limit of sums. The anti-derivative connection comes later." That one sentence avoids the common belief-blurring that would otherwise contaminate the FTC scene.

## Gotchas / anti-patterns

- **Proofs without pictures.** Product rule derived algebraically is a symbol dance; with the rectangle-area picture, it's memorable. Same for FTC.
- **ε–δ before the intuitive limit.** The formalism presupposes knowing what it's formalising. If a user prompts directly for ε–δ, the curriculum agent should still place intuitive-limit first unless explicitly overridden.
- **Using `f'(x)` when `dy/dx` carries the pedagogy.** And vice versa. Notation is a pedagogical tool, not decoration.
- **Reusing a dummy variable as a free variable.** `∫_0^x f(x) dx` is a correctness hazard; use `t` inside.
- **Treating "derivative of position" and "derivative as slope" as duplicate topics.** They're complementary anchors; both belong in a general derivatives pack, but a single video picks one and stays with it.
- **Over-packing.** Chain rule + product rule + quotient rule in one video = three derivative rules, way over the cognitive-load budget. Each gets its own video.
- **Series in Phase 1.** The last group is present in this pack for completeness but not in the Phase-1 regression set. If a user prompts for Taylor series, the curriculum agent should flag the request as beyond Phase-1 scope rather than over-commit.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. 20 topics in 5 groups; full per-topic content for the 10 Phase-1 regression targets; notation conventions and prerequisite graph.
