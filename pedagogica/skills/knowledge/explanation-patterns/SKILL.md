---
name: explanation-patterns
version: 0.1.0
category: pedagogy
triggers:
  - stage:curriculum
  - stage:storyboard
  - stage:script
requires:
  - pedagogy-sequencing@^0.1.0
token_estimate: 2400
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Three canonical explanation patterns (define→motivate→example→generalize,
  compare/contrast, first-principles build-up) plus decision rules for picking
  which pattern a beat should use and how to close a video. Composes with
  pedagogy-sequencing: sequencing tells you the order of ideas; patterns tell
  you the shape of a single beat.
---

# explanation-patterns

## Purpose

A Pedagogica video is a sequence of beats. `pedagogy-sequencing` decides what the beats are and what order they run in. This skill decides what *shape* each beat has internally — the rhetorical pattern that carries the idea from the start of the beat to the end. Agents that draft curricula, storyboards, or scripts choose a pattern per beat and fill in its slots.

Three patterns cover ~90% of Phase-1 calculus needs. A fourth family — closing-beat patterns — applies to the last 15–20 s regardless of what came before.

## When to load

- Curriculum agent — **always**. Patterns inform the per-LO outline.
- Script agent — **always**. The pattern's skeleton becomes the narration scaffold.
- Storyboard agent — **conditional**. Load if the storyboard needs to pick patterns per beat (usually yes for calculus; skippable for a straight demo reel).
- Script-critic — **always**, paired with `pedagogical-critique`, so the critic can name which pattern was attempted and where it drifted.

Composes with `pedagogy-sequencing`: pick the sequence first, then for each beat choose a pattern.

## Core content

### Pattern A — define → motivate → example → generalize (DMEG)

The workhorse. Use when a single concept needs to land.

| Slot | Purpose | Typical length (in a 30 s beat) |
|---|---|---|
| **Define** (weak) | A provisional description in plain language, not a formal definition. One sentence. Prepares the viewer to notice the thing. | 3–5 s |
| **Motivate** | A question the viewer now wants an answer to. Often: "why would you want a number like that?" | 4–7 s |
| **Example** | The anchor example (picked per `pedagogy-sequencing`) worked through concretely. | 12–18 s |
| **Generalize** | Replace the specifics with variables. Name the concept formally. Optionally introduce notation. | 5–8 s |

Note the order: definition is *provisional* and goes first only to scaffold. The *formal* definition (with notation) is in the generalize slot. This is subtle — calling both "definition" is a trap.

Shape-fitting check: if a beat can't be phrased as "here's a rough idea → here's why you care → here it is concretely → here's the clean version," it probably needs a different pattern.

### Pattern B — compare / contrast

Use when the concept is best understood against a neighbour — a previously-taught idea it resembles but differs from.

| Slot | Purpose |
|---|---|
| **Restate neighbour** | Remind the viewer of the idea being contrasted, briefly. |
| **Place new idea alongside** | Introduce the new idea in parallel structure to the neighbour. |
| **Diff** | Name the difference(s). Visualise the difference. |
| **When each applies** | The part most often skipped. Give a one-sentence heuristic for which to reach for when. |

Canonical calculus uses:

- Average rate of change vs. instantaneous rate of change.
- Definite integral vs. indefinite integral.
- Derivative of a sum vs. derivative of a product (setting up why product rule is non-obvious).
- Limit from the left vs. limit from the right (one-sided limits).

Why it works: the neighbour provides a prior-knowledge scaffold, so the new idea only needs to encode the delta. Cognitive-load-efficient.

Why it fails if mis-used: comparing two things the viewer doesn't already hold. If the "neighbour" is itself new, compare/contrast becomes "teach two things at once" — a sequencing violation.

### Pattern C — first-principles build-up

Use when the payoff is insight, not just utility. The beat derives the idea from a simpler truth the viewer already trusts.

| Slot | Purpose |
|---|---|
| **Stand on firm ground** | State a prior truth the viewer accepts. |
| **Ask a step-over question** | "What if we push this a little further?" |
| **Take the step** | A single deductive or constructive move. One step — not a chain. |
| **Land** | The new idea is the destination of that step. Name it. |

Canonical uses in Phase 1 calculus:

- ε–δ from "we can make the output as close to L as we want by making x close enough to a."
- The Fundamental Theorem of Calculus from "area is an antiderivative of the height function."
- Riemann sum → integral: from "rectangles approximate area" to "the limit of the approximation *is* the area."

Why it works: the insight lands *because* the viewer sees it happen, not because they're told. The named concept inherits the credibility of the prior truth.

Why it's risky: the single step must genuinely be one step, not a smuggled chain. If the derivation takes more than one move, it's not a first-principles beat — it's a mini-proof, which belongs in a different video (or a compare/contrast with the prior result).

### Pattern choice (decision rule)

Given a beat's `beat_type` (from `SceneBeat.beat_type`):

| Beat type | Default pattern | When to override |
|---|---|---|
| `hook` | Curiosity-first variant of DMEG (lead with motivate, skip define) | Never open with compare/contrast — no neighbour yet. |
| `define` | DMEG | Use C (first-principles) if the definition is best earned rather than stated. |
| `motivate` | C (first-principles) | Use DMEG if the motivation is utilitarian ("you need this to compute X"). |
| `example` | DMEG with a heavy example slot | Compare/contrast if a parallel example makes the point sharper. |
| `generalize` | Generalize-only (abbreviated DMEG: skip the earlier slots, they ran in prior beats) | — |
| `recap` | Closing pattern (below) | — |

### Closing-beat patterns

The final 15–20 s of the video. One of:

- **Recap**: restate the spine of what was shown in 2–3 sentences. Default choice.
- **Punchline**: one surprising consequence of what was just built. Use when the topic has a small, clean "aha." (Good for: FTC, chain rule.)
- **Cliffhanger**: name the next question this opens. Use sparingly; only if a follow-up video is planned or the question is famous. (Good for: ε–δ closing on "now we can prove uniqueness of limits.")

Whichever you pick, close on the anchor example. New examples in the closer disorient.

## Examples

### Example 1 — DMEG (derivative as slope, 30 s beat)

- **Define (provisional)**: "The derivative is a way to measure how fast something is changing at a single moment."
- **Motivate**: "The slope between two points is easy. But what if the two points are the same point?"
- **Example**: Anchor `y = x²`. Two moving points slide together; secant rotates toward tangent; slope number converges to `2` at `x = 1`.
- **Generalize**: "In general: `f'(x)` is the slope of the tangent to `y = f(x)` at `x`. Our example: `f'(x) = 2x`."

### Example 2 — Compare/contrast (average vs. instantaneous rate)

- **Restate neighbour**: "Average speed between time 0 and 5 is distance travelled divided by 5."
- **Place new idea alongside**: "Instantaneous speed at time 2 is… what divided by what?"
- **Diff**: "We shrink the interval down to nothing. The ratio of shrinking distance to shrinking time has a limit — and that limit is the instantaneous speed."
- **When each applies**: "Average speed answers 'how long did the trip take?'. Instantaneous speed answers 'how fast was the speedometer reading?'."

### Example 3 — First-principles (FTC part 1, lean)

- **Stand on firm ground**: "Area under a curve can be built up by sweeping a vertical bar from left to right."
- **Step-over question**: "As the bar sweeps, how fast does the area grow?"
- **Take the step**: "Right at any x, the area is growing at exactly the height of the curve at x."
- **Land**: "So the running-area function has a derivative equal to the original function. That's the Fundamental Theorem."

### Counter-example — pattern salad

A beat that tries DMEG for the first half, compare/contrast for the second, and closes with a punchline — 30 s is not enough for one of those, let alone three. The viewer gets frag-frag-frag. Fix: pick one, cut the others.

## Gotchas / anti-patterns

- **Mis-labelling "define" as the formal version.** The first slot of DMEG is informal. The formal version is the generalize slot.
- **Compare/contrast without a held neighbour.** If the "neighbour" is itself being introduced in the same video minutes earlier, make sure it had time to settle (≥ 1 other beat between).
- **Multi-step first-principles.** If the derivation has two moves, it's not pattern C. Split into two beats or pick a different pattern.
- **Pattern-hopping mid-beat.** One pattern per beat. The *video* can use many; a beat cannot.
- **Opening with compare/contrast.** No neighbour exists yet; use DMEG or first-principles.
- **Closing with a new example.** Return to the anchor. New examples belong in the middle.
- **Skipping "when each applies" in compare/contrast.** It's the part that makes the distinction useful; without it, the viewer remembers there are two things but not how to choose.
- **Over-using cliffhanger.** Rewards the creator (feels punchy) but often leaves the viewer unresolved. Default to recap.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. Three core patterns + closers + decision rule keyed on `SceneBeat.beat_type`. Worked examples aligned with `pedagogy-sequencing`'s anchor picks.
