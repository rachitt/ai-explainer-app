---
name: spoken-narration-style
version: 0.1.0
category: narration
triggers:
  - stage:script
  - stage:script-critic
  - stage:sync
requires:
  - pedagogy-cognitive-load@^0.1.0
  - explanation-patterns@^0.1.0
token_estimate: 2300
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  How to write English narration that works for a single-narrator TTS video:
  sentence shape for the ear, signposting that a listener can follow without
  a scrollback, redundancy budget, breath points, and the tokenization
  contract with Script.words / Script.markers. Used by the script agent to
  draft, by the script-critic to review, and consulted by sync when markers
  need to be re-anchored to word indices.
---

# spoken-narration-style

## Purpose

A reader can re-read a clotted sentence. A listener cannot. Pedagogica narration is heard once, at whatever pace ElevenLabs chose, while the viewer is also parsing a visual. This skill is the craft of writing for that channel: sentences that land on first hearing, signposts that the ear picks up as signposts, repetition used as a memory aid rather than padding, and breath points that give the concept a moment to settle before the next one arrives.

It is the sibling of `pedagogy-cognitive-load` (which caps *how much* a beat can hold) and `explanation-patterns` (which shapes the beat). Where those govern structure, this skill governs the sentence-level surface that the TTS actually speaks.

## When to load

- Script agent — **always**. First-draft narration must be written against these rules, not patched into them afterwards.
- Script-critic — **always**, paired with `pedagogical-critique`. The critic cites specific rules here when flagging.
- Sync agent — **conditional**. Load when a marker's `word_index` no longer lines up after a narration rewrite and the sync agent needs to re-anchor by meaning rather than by offset.
- Do not load for visual, layout, or Manim codegen agents — they don't emit narration.

## Core content

### 1. Sentence shape

- **Aim for 8–16 words.** Below 8 reads as fragments; above 16 starts forcing the listener to hold clauses open. Occasional 20-word sentences are fine if they're the payload sentence of a beat and land on a pause.
- **One main clause, at most one subordinate.** This is the Rule 3 ceiling from `pedagogy-cognitive-load`; the narration-style corollary is that the subordinate clause should trail the main clause, not precede it. "The slope approaches a limit, as the two points slide together" reads better spoken than "As the two points slide together, the slope approaches a limit." The ear needs the subject first.
- **Avoid mid-sentence interpolations.** Em-dash asides and parenthetical clauses disappear in speech. If it's worth saying, give it its own sentence.
- **Put the important word at the end.** End-weight is the single strongest emphasis tool the text has over a single-voice TTS. "That limit is the derivative." lands; "The derivative is that limit." does not.

### 2. Signposting

The listener has no scroll bar. Signposts are the verbal cues that tell them where in the argument they are.

Four signpost families, in rough order of frequency:

- **Orienting**: "Here's the idea.", "Start with a curve.", "Consider two points." — used at the start of a beat or a new thought.
- **Progressing**: "Now watch.", "Notice what happens.", "And then…" — used when the animation is about to do something load-bearing.
- **Landing**: "That's the derivative.", "So the slope is exactly two x.", "This is the limit we wanted." — the payload sentence; anchored by a pause.
- **Returning**: "Back to our parabola.", "Remember the slope from before." — used sparingly, only when a visual call-back isn't enough.

Rule: at least one signpost per beat, rarely more than three. A script that uses no signposts reads fine on the page and loses the listener at 45 seconds.

### 3. Redundancy budget

Spoken-word explanations tolerate — and *require* — more repetition than written text. But the redundancy has to do work.

Three forms of allowed repetition:

- **Echo-naming**: after formally naming a concept, restate it in plain terms once. "That's the derivative. That's the slope of the tangent, right there." Echo-naming earns the name its first usage.
- **Verbal call-back**: mentioning an object just as the visual returns to it. Lines the ear up with the eye.
- **Parallel structure across scenes**: two beats that share a rhythm ("we did this for x², now we do it for x³") let the listener carry forward the shape.

Three forms that waste the budget:

- **Saying and writing the same formula simultaneously** ("the derivative of x squared is two x" while `f'(x)=2x` is being written on screen). Pick one channel per moment.
- **Restating the sentence just spoken** with different words but no new content. Feels like padding; is.
- **Preambles** ("What we're going to look at next is…"). The scene transition already did that job; the narration should start with the content.

### 4. Breath points

Not silence for its own sake — a deliberate gap that lets the listener catch up. Handled mechanically by `pacing-rules`; the narration-side rule is simpler:

- **End punctuation is a breath cue.** Write periods where you want the TTS to breathe. ElevenLabs honours them.
- **Break long thoughts across two sentences instead of using a comma.** "The slope between two points is easy. It's rise over run." beats "The slope between two points is easy, which is rise over run."
- **Never write a comma-spliced sentence for TTS.** They read as one long breath and reliably trip the voice into an unnatural cadence.

### 5. The tokenization contract with `Script`

`Script.words` is the tokenized view of `Script.text` and is the single source of truth for `ScriptMarker.word_index`. Word indices are zero-based and include every token the tokenizer emits.

Rules the script agent must respect when writing `text`:

- **Contractions count as one word.** "don't" is one word, not two. The tokenizer is whitespace-based.
- **Numerals count as one word.** "2x" is one word. Spell out when you want separate anchoring: "two x" = two words.
- **Hyphenated compounds are one word.** "rate-of-change" = one word; "rate of change" = three. Pick based on whether you need to anchor a marker mid-phrase.
- **LaTeX source never appears in `text`.** Narration text is spoken; LaTeX goes in the visual. Say "f prime of x" or "the derivative", never `f'(x)`.
- **Pauses are markers, not punctuation tricks.** Use `ScriptMarker(marker_type="pause", word_index=N)`. Don't try to inject `...` into the text and hope the TTS interprets it.

Markers anchor visual events to narration words. The script agent should place them at the word the viewer should be *looking at the element while hearing*. If the visual plan highlights the tangent line, place the `show` marker at the word "tangent", not at the start of the sentence.

### 6. Voice

One narrator, undergraduate register, confident but not swaggering. Three micro-rules:

- **First-person plural ("we") is fine; first-person singular ("I") is not.** "We slide the points together" invites the viewer in; "I'll slide the points" doesn't.
- **No hedging without reason.** "Maybe the slope approaches something like a limit" is worse than "The slope approaches a limit." Hedge only when the narration is genuinely signalling uncertainty (rare in Phase 1 calculus).
- **No metacommentary on the medium.** "As you can see in this animation" is filler; the animation is doing the seeing. Just describe the object.

## Examples

### Example 1 — rewrite pass on a draft sentence

Draft: "As we slide the two points together along the curve, which is the parabola y equals x squared that we introduced earlier, the slope of the secant line between them, which is just rise over run, approaches a specific value, namely 2, which is the derivative at x=1."

Problems: 48 words, three subordinate clauses, mid-sentence interpolations, LaTeX-ish `x=1` in the narration, and the payload ("the derivative at 1 is 2") buried in the middle.

Rewrite (4 sentences, signposted):

> Slide the two points together. The slope between them is just rise over run. As they get close, it approaches a single number. At x equals one, that number is two.

22 words less, all rules satisfied. The payload lands at the end.

### Example 2 — redundancy used well

> The slope approaches a limit. [pause] That limit — the slope at a single instant — is the derivative.

The second sentence *echo-names* the idea ("slope at a single instant") right after naming it formally ("derivative"). The listener heard the formal name once; now they have the plain version to hold on to. The em-dash here is spoken as two short pauses, which the TTS handles cleanly.

### Example 3 — marker anchoring

Narration: `"Watch the slope as the interval shrinks to zero."`
Tokens (`Script.words`): `["Watch", "the", "slope", "as", "the", "interval", "shrinks", "to", "zero."]`

Markers:
- `ScriptMarker(word_index=2, marker_type="highlight", ref="label.slope")` — highlight slope label on the word "slope".
- `ScriptMarker(word_index=5, marker_type="show", ref="arrow.interval")` — the interval arrow appears on "interval".
- `ScriptMarker(word_index=8, marker_type="pause", ref="beat.landing")` — 0.8 s pause after "zero." — let the idea settle before the next sentence.

### Counter-example — preamble + meta + hedge

> "So, what I'm going to try to show you in this next little bit is maybe something like how the derivative could be thought of as a slope — or at least that's one way to look at it."

Preamble ("what I'm going to try to show"), first-person singular, metacommentary ("in this next little bit"), triple hedge ("maybe", "could be thought of", "one way to look at it"). 32 words to say "the derivative is a slope." Cut all of it.

## Gotchas / anti-patterns

- **Drafting on the page.** Write, then read aloud at natural pace. Clotted sentences reveal themselves in the mouth before they do on the page.
- **Signpost inflation.** Three signposts per beat is the ceiling; a script with a signpost every sentence reads as a lecture transcript, not an explanation.
- **Putting the concept name at the start of the sentence.** End-weight is earned; squandering it on the first word means the landing never happens.
- **Commas instead of periods.** Every comma that could be a period in spoken prose should be a period. TTS breathes on periods.
- **LaTeX or notation in `text`.** If the listener would hear the backslash, it's wrong. Say the thing; let the visual show the symbol.
- **Misaligned markers.** Markers placed at sentence starts or sentence ends — rather than at the content word — produce a visual that moves at the wrong moment. The ear notices.
- **Hedging the payload.** The landing sentence should be declarative. Never hedge the thing you spent the beat earning.
- **Echo-naming that doesn't echo.** If the plain-language restatement adds new information, it's a new sentence, not an echo — budget it as one.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. Sentence shape, signposting, redundancy, breath points, tokenization contract with `Script`. Worked examples on rewrite, echo-naming, and marker anchoring. Paired with `pacing-rules` for the pause mechanics.
