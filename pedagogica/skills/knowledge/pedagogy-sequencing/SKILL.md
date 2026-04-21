---
name: pedagogy-sequencing
version: 0.1.0
category: pedagogy
triggers:
  - stage:curriculum
  - stage:storyboard
  - stage:script
requires: []
token_estimate: 2200
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  How to order concepts inside a 2–4 minute explainer: when to introduce notation,
  how to progress from concrete instance to general rule, and how to choose the
  scene that earns the viewer the right to care. Used by the curriculum agent
  to sequence learning objectives and by the storyboard agent to decide scene
  order within a single topic.
---

# pedagogy-sequencing

## Purpose

A video explains a concept; the sequence decides whether that explanation lands. The same facts in a different order become a different lesson — sometimes a good one, often a confusing one. This skill gives the agent the decision rules for ordering: what shows first, what gets a name, when the general form appears, and how to tell a coherent arc from a reference-book dump.

The rules here are small and cheap to apply. They're also the most common source of shallow storyboards when missing.

## When to load

- Curriculum agent — **always**, alongside `explanation-patterns`, `pedagogy-cognitive-load`, and the domain pack.
- Storyboard agent — **always**, to order scene beats.
- Script agent — load when a scene's narration needs to re-introduce a prior concept or build a bridge to the next scene.
- Do not load for visual tier (placement, colors) or audio tier — ordering is upstream of those.

## Core content

### The three heuristics (in priority order)

#### 1. Name after show

> Demonstrate the idea with a concrete instance first. Only name it after the viewer has seen it *happen*.

Calc example: draw a curve, slide a secant line down to a point, *then* say "this is called the derivative at that point." Not: define the derivative symbolically, *then* show the picture.

Why: a name is a cognitive handle. Handles are useful only if there's something to hold. Naming first asks the viewer to allocate working memory for an empty box, hope the next sentence fills it, and hold the box open while they parse the fill. Showing first means the name arrives as a compression of something already held.

When to break the rule: when the name is so common (`f(x)`, `+`, `=`) that the viewer already has it. Even then, prefer *re-grounding* the familiar name in a fresh visual before using it as a new primitive.

#### 2. One thread at a time

> A scene beat introduces *one* new idea. Complications are later scenes.

"New idea" = a new concept, a new notation, a new sub-result, or a new perspective on an old one. Limit to one per beat. If a beat seems to need two (common temptation: introduce the chain rule *and* the composition notation simultaneously), split into two beats.

Why: conceptual novelty competes for the same working-memory channel as following the visual and parsing the narration. Two at once means neither is retained. This dovetails with `pedagogy-cognitive-load`'s 20–30-s rule but is a separate constraint: cognitive load is about volume, sequencing is about threading.

When to break the rule: when two ideas are genuinely the two halves of a single idea (e.g. "the derivative as a number" *and* "the derivative as a function of x" in the same beat that motivates *why* they're the same thing). Rare.

#### 3. Backwards from the goal

> Write the sequence by starting at the terminal learning objective and walking backwards. Each step becomes a prerequisite. That's your order.

Procedure:
1. State the LO: e.g. "viewer can compute the derivative of a composition using the chain rule."
2. Ask: what must the viewer already believe to accept this? List: derivatives are slopes; the derivative is linear; derivatives measure sensitivity to small changes; `f(g(x))` is a well-defined operation.
3. For each prerequisite: is it assumed, or must the video build it? If build: recurse — what must the viewer believe to accept *that*?
4. The sequence is the reverse of this descent: earliest build first, LO last.

Why: the natural planning failure is to start with "derivative is slope" because it feels like the right opener, without checking that it actually supports the LO. Walking backwards keeps every scene *on the line* to the goal.

### Choosing the anchor example

Every topic needs one concrete example that carries the motivating intuition. Picking it is a sequencing decision because the whole sequence hangs off it.

Choose an anchor that is:

- **Unambiguously computable.** The viewer can, in principle, check the numbers. A parabola `y = x²` is a classic anchor for derivatives because the slope-at-each-point has a clean closed form.
- **Visually generous.** The example should have something to *show*, not just something to say. A continuously-varying slope, a shrinking interval, a morphing shape — the anchor earns its keep by animating.
- **Not a special case.** Avoid examples that work only because of a quirk (e.g. `y = x` for derivatives — slope is constant, so nothing moves).
- **Re-usable across the video.** If the second scene can reuse the anchor from the first with a new overlay, that's a sequencing win: the viewer doesn't pay the cost of orienting to a new example.

### Notation introduction

Notation is a subset of naming; the same "name after show" rule applies, but more strictly because notation persists on screen.

- Operational first, symbolic second. Before `f'(x)`, show "the slope at this point" with an arrow and a number. After 15–30 s of operational use, introduce `f'(x)` as shorthand for exactly what was being shown.
- Don't teach two notations for the same thing in one scene. `dy/dx` and `f'(x)` for derivatives both belong; introduce the second only in a later scene that motivates why you'd want it (e.g. when chain rule's `dy/du · du/dx` needs Leibniz).
- Never emit a new piece of notation and use it in the same sentence. Let the notation breathe for at least one beat.

### Recap and bridging

- A 2–4 min video needs at most one mid-video recap (end of "build up" section, before "generalize"). Any more and recaps crowd out new content.
- Inter-scene bridges are short (1 sentence). Their job is to connect the last beat's takeaway to the next beat's question, not to re-state.
- The closing beat returns to the anchor example; closing on a fresh example is disorienting.

## Examples

### Example 1 — Good sequence (derivative as slope)

1. **Hook**: draw `y = x²`; place two moving points on the curve; show the line connecting them (secant) and the slope number.
2. **Pull them together**: slide the two points closer; slope number updates live; visually, secant rotates toward the tangent line.
3. **Name it**: "the number the slope approaches — that's the derivative at this point."
4. **Give the symbol**: `f'(x)` as shorthand. `f'(1) = 2`, `f'(2) = 4`. Show the pattern.
5. **Generalize**: `f'(x) = 2x`. Recap the anchor. Done.

Why it works: anchor is `y = x²` (computable, visual, not a special case). "Name after show" applied twice — concept then notation. One thread per beat. Sequence walks forward but was designed by walking backward from the LO ("compute the derivative of a polynomial").

### Example 2 — Broken sequence (same topic, bad order)

1. "The derivative is defined as `lim_{h→0} (f(x+h) - f(x))/h`." [formula + limits + notation, all at once]
2. "Let's see an example: `y = x²`."
3. "So `f'(x) = 2x`."
4. "Geometrically, this is the slope of the tangent line."

Why it fails: names everything before showing anything. Puts the limit notation (the *hardest* piece) first. Geometry — the motivating intuition — is a footnote. Viewer who didn't already know this leaves confused; viewer who did know it learns nothing.

### Example 3 — Anchor-choice call

LO: "viewer understands the product rule." Anchor options:
- `f(x) = x · sin(x)` — visual (product of two familiar curves), differentiable by product rule, result is non-trivial.
- `f(x) = x · x` — computable but special (collapses to `x²`; product-rule derivation looks circular).
- `f(x) = x² · e^x` — honest product but `e^x` is a distraction if exponentials haven't been in the prereqs.

Choose option 1.

## Gotchas / anti-patterns

- **Definition-first openings.** "The derivative is the limit of…" before the viewer has been given a reason to want a number like that. Invert: show the phenomenon, then say "we need a number for this."
- **Pre-emptive generality.** Stating the general rule before doing an instance. The general form is the *last* beat, not the first.
- **Simultaneous concept + notation.** Introducing the idea and its symbol in the same sentence. Split them by at least a sentence, better by a beat.
- **Scope creep per scene.** When a scene accumulates "oh and also…" clauses, it has two threads; split.
- **Re-using a broken anchor.** If the anchor example is a special case, no amount of good sequencing downstream saves the video.
- **Skipping the motivating scene.** The "why should I care" beat is not optional for a cold-start viewer, even in undergrad content.
- **Backwards-from-goal executed once.** Do it again after drafting. First pass usually finds the obvious prereqs; second pass finds the subtle ones.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. Three heuristics + anchor/notation/recap rules. Worked examples on derivative-as-slope and product rule.
