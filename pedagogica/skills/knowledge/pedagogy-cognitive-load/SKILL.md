---
name: pedagogy-cognitive-load
version: 0.1.0
category: pedagogy
triggers:
  - stage:curriculum
  - stage:storyboard
  - stage:script
  - stage:visual-planner
requires: []
token_estimate: 1900
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Budget rules for the viewer's working memory across a 2–4 minute video:
  one new concept per 20–30 seconds, at most three simultaneous highlights,
  at most two sub-clauses per spoken sentence, pause placements that let
  ideas settle. Used by every agent that decides *how much* to pack into a
  beat — curriculum, storyboard, script, visual planner.
---

# pedagogy-cognitive-load

## Purpose

A viewer has a fixed working-memory budget per unit time. The video that tries to spend more of it than the viewer has produces confusion, not education. This skill is the numeric budget — simple, enforceable rules for how much new material a beat can introduce, how many things can be salient at once, and when to pause. It is deliberately quantitative; pedagogy arguments about "pacing" collapse into decisions the agent can apply.

Pairs with `pedagogy-sequencing` (which governs *what* order) and `explanation-patterns` (which governs *what shape* a beat takes). This skill governs *how much*.

## When to load

- Curriculum agent — **always**. The number of LOs per minute of video is a cognitive-load decision.
- Storyboard agent — **always**. Scene durations and number of scenes fall out of these rules.
- Script agent — **always**. Sentence length and pause marking use the rules directly.
- Visual planner — load when a scene has more than ~6 elements; the "simultaneous salience" rule constrains the animation plan.
- Manim-code agent — not needed; animation choices are already constrained upstream.

## Core content

### The four numeric rules

Each rule has a **soft target**, a **hard cap**, and a **why**. Soft targets are where the video should sit on average; hard caps are where a single beat stops being defensible.

#### Rule 1 — One new concept per 20–30 seconds

- **Soft target**: one new concept every 25 s.
- **Hard cap**: no more than one new concept per 15 s sustained; a brief spike (two concepts in 20 s) is allowed once per video if one of them is a re-grounding of prior material.
- **Why**: a new concept needs about 20 s of exposure to move from "heard" to "held" in working memory. Introducing the next one before that consolidates forces the viewer to choose which to track.

A "new concept" is: a new definition, a new notation, a new rule, or a new *perspective* on an old concept (e.g. moving from "derivative as slope" to "derivative as rate of change" is a new concept even though the object is the same).

Implication for Phase 1 (180–240 s videos): **6–10 new concepts total**, no more.

#### Rule 2 — Three simultaneous highlights

- **Soft target**: at most 2 highlighted elements on screen at the same frame.
- **Hard cap**: 3.
- **Why**: a highlight (colour change, scale, arrow, label) directs attention. Multiple simultaneous highlights split attention; above 3, the viewer stops tracking them as a set and starts seeing decorative noise.

Rest frames — frames with no animation happening — tolerate more elements, but no more than ~5 salient pieces per Miller's 7±2 restated for video. Decorative elements (axes, neutral labels) don't count against this.

Implication for the visual planner: when a beat's animation plan would highlight 4+ elements concurrently, either stagger them (serialise via `run_after`) or drop one.

#### Rule 3 — Spoken sentences: ≤ 2 sub-clauses

- **Soft target**: one main clause plus at most one subordinate clause per spoken sentence.
- **Hard cap**: two subordinate clauses, but only if the sentence is shorter than 15 words.
- **Why**: speech is linear; the listener can't re-read. Long compound sentences force them to hold early clauses open while parsing later ones. Every retained clause is a slot in working memory not available for the concept itself.

Heuristic: if a sentence reads fine silently but feels clotted when you say it aloud at natural pace, it's too long.

#### Rule 4 — Pauses

- **Soft target**: 0.5–1.5 s pause after every "landing" sentence (a sentence that delivers a key takeaway).
- **Hard cap**: no beat goes more than 20 s without a pause ≥ 0.4 s.
- **Why**: pauses are where consolidation happens. Dense narration without pauses reads as "information firehose"; the viewer disengages before the next point lands.

Where to place pauses:

- After a formal generalisation names the concept.
- Before a transition to a contrasting idea.
- At scene boundaries (the sync agent typically adds 0.3–0.5 s at boundaries automatically; the script's own pause markers are on top of that).
- After a punchline in a closing beat.

### Chunking

When several small steps compose into a sub-result, name the sub-result and use it as a single unit downstream. "We showed the slope is `2x`; now we'll use that." beats restating the derivation.

Chunking reduces the effective concept count: a 4-step derivation, once named, becomes one concept for subsequent beats. This is the main lever for staying under Rule 1 when a topic genuinely has many moving parts.

### Screen density at rest

A rest frame (no animation active) should have:

- ≤ 5 salient pieces (equations, labelled objects, key shapes).
- ≤ 12 total objects including decoration (axes gridlines, ticks, neutral labels).
- No duplicate information — if an equation is on screen and the narration is about to say it aloud, the written form is already there; don't then animate writing it out again.

### Cross-rule composition

The rules interact. A script that stays under Rule 3 but packs three new concepts into 30 s fails Rule 1; a visual plan with two highlights and a dense rest frame fails Rule 2's rest-frame tail. The budget is joint, not marginal — the agent should check all four rules against the same beat.

## Examples

### Example 1 — Beat under budget

30 s beat, DMEG pattern, derivative-as-slope:
- 1 new concept ("derivative"). Rule 1: ✓.
- Peak simultaneous highlights: 2 (secant arrow + slope number). Rule 2: ✓.
- 4 sentences, longest 13 words, one subordinate clause each. Rule 3: ✓.
- 1 pause of 0.8 s after naming the concept. Rule 4: ✓.

### Example 2 — Beat over budget (fix needed)

30 s beat aiming to teach product rule:
- Concepts introduced: product rule, its formula, a worked example, a comparison to the sum rule. **4 concepts → fails Rule 1.**
- Peak highlights: 5 (two function curves, two derivative labels, a sum-indicator). **Fails Rule 2.**
- Sentences average 22 words with 3 clauses. **Fails Rule 3.**

Fix: split into three beats. Beat A: name the question ("why isn't the derivative of a product just the product of the derivatives?"). Beat B: state the rule with a 2-term example. Beat C: apply to a harder example. Each beat handles one concept; highlights drop to 2–3; sentences shrink.

### Example 3 — Pause placement

Script fragment with pauses marked (`||` = 0.8 s pause, `|` = 0.4 s):

> The slope between these two points is easy to compute. | It's just rise over run. Now watch what happens as we slide the points together. ||
> The slope approaches a limit. || *That* limit — the slope at a single instant — is the derivative. ||

Four pauses in ~14 s of narration. Two `||` after landings, two `|` at natural breath breaks. This beat stays under Rule 4's 20 s cap comfortably.

## Gotchas / anti-patterns

- **Counting notation as "not a concept."** `dy/dx` is a concept the first time it's introduced, even if the underlying idea is already held.
- **Treating simultaneous highlights as free if they're the "same colour."** Colour coherence helps, but attention still splits if the elements are spatially separate. Three blue arrows is still three highlights.
- **"Dense but clear."** A sentence that is logically clean but 30 words long still fails Rule 3. Clarity in syntax is not the same as clarity in cognition.
- **Zero-pause scenes.** Scripts read as prose drafts often have no pauses. The script agent must insert them deliberately.
- **Rest-frame clutter.** When a scene has done its work, un-highlighted elements linger. At the beat's end, fade non-essentials before moving on.
- **Chunking without naming.** Compressing a derivation into one line without giving the result a memorable name forfeits the chunking benefit — downstream beats can't reach the compression.
- **Spiking twice per video.** The "one spike allowed" rule means *one*. Two is a systemic over-budget, not two isolated exceptions.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. Four numeric rules + chunking + density constraints. Examples at the budget and over the budget.
