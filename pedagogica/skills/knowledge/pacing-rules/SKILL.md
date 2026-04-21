---
name: pacing-rules
version: 0.1.0
category: audio
triggers:
  - stage:script
  - stage:sync
  - stage:tts
requires:
  - pedagogy-cognitive-load@^0.1.0
  - spoken-narration-style@^0.1.0
token_estimate: 2100
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Mechanics of tempo across a 2–4 minute explainer: where pauses go, how long
  they should be, how to vary speaking rate across beat types, and how the
  script's pause markers reconcile with ElevenLabs' natural breath insertion
  plus the sync agent's wait() padding. Used by the script agent to place
  pause markers, by the sync agent to decide wait_after_seconds, and by the
  TTS helper to pick a model/stability that honours the marks.
---

# pacing-rules

## Purpose

A Pedagogica video has three pacing actors: the script (where pauses are marked), ElevenLabs (which inserts its own breath and breaks punctuation into micro-pauses), and the sync agent (which adds `wait_after_seconds` between animations). Left uncoordinated they fight — the script marks a 0.8 s pause at a landing, ElevenLabs adds its own 0.4 s on the period before it, and sync pads another 0.5 s after the last animation ended early. Viewer gets 1.7 s of dead air on a beat that should have had 0.8.

This skill is the coordination contract. It covers the numeric budget for pauses, the model of what "a pause" actually is in the pipeline, and how each agent's decisions compose with the others'. It extends Rule 4 of `pedagogy-cognitive-load` from "where" to "how exactly."

## When to load

- Script agent — **always**. Marker placement (`ScriptMarker.marker_type == "pause"`) comes from here.
- Sync agent — **always**. `wait_after_seconds` and `audio_offset_seconds` in `SyncPlan` use these rules.
- TTS helper (`pedagogica-tools elevenlabs-tts`) — **always as a config doc**, to pick model + stability settings that respect script-inserted pauses.
- Script-critic — **conditional**; load when reviewing a beat for "feels rushed" or "drags" complaints.
- Do not load for pure visual agents — they don't emit timing.

## Core content

### 1. The three pause sources, and how they compose

Every silent gap in the final audio has one of three origins:

1. **Authored pauses** — `ScriptMarker(marker_type="pause", word_index=N)`. Intent: deliberate beats. Target lengths 0.4 s / 0.8 s / 1.5 s (see §2).
2. **TTS-natural pauses** — ElevenLabs inserts ~50–300 ms on sentence-final punctuation (`.`, `!`, `?`) and ~80–150 ms on clause breaks (`,`, `;`, `—`). Model-dependent. Always shorter than 0.4 s.
3. **Sync padding** — `wait_after_seconds` inserted by the sync agent when the visual overruns its anchored word, or when the scene boundary needs settle time (fixed 0.3 s at every scene-end in Phase 1).

**Composition rule**: at any one point in time, a gap comes from one source only. If an authored pause falls on a sentence-final period, its length *replaces* the TTS-natural pause, not adds to it. If sync padding lands on the same word as an authored pause, the sync agent uses `max(authored, padding)`, not the sum.

The TTS helper achieves this by consuming the authored-pause markers *before* sending text to ElevenLabs: it splits the text at the marker, requests each segment separately, and inserts `AudioClip` silence of the authored length between segments. That inserted silence supersedes whatever ElevenLabs would have added at that sentence-end.

### 2. The three pause lengths

Phase 1 uses exactly three lengths. Anything in between gets rounded to the nearest.

| Name | Seconds | Use |
|---|---|---|
| **Micro** | 0.4 s | Breath break mid-beat; between two related sentences where the second elaborates the first. |
| **Landing** | 0.8 s | After a sentence that delivers the beat's payload. One or two per beat. |
| **Scene gap** | 1.5 s | End-of-scene settle. The sync agent adds this automatically at scene boundaries; the script should *not* mark a scene-final pause — it would double-count. |

Three lengths, not a continuous scale, because the regression signal is cleaner: critic scores correlate with pause discipline, and "0.62 s pause" isn't a category the rubric can reason about.

### 3. Per-beat pause budget

A 30 s beat should have:

- **1–2 landing pauses** (0.8 s each). More than 2 starts to drag.
- **0–3 micro-pauses** (0.4 s each).
- **No scene-gap pause** — that's at the boundary, not inside.

Total silence inside a beat: ~1.0–2.5 s. A beat with <0.8 s of total silence will feel rushed; a beat with >3.0 s will feel slow, regardless of how well the content is sequenced.

Implication for script-agent output: every beat gets at least one pause marker. A beat with zero markers is the bug, not the exception.

### 4. Speaking rate by beat type

ElevenLabs `eleven_multilingual_v2` at default stability speaks at ≈ 2.4 words/second for English undergrad narration. Phase 1 holds stability fixed (tested value, don't tune per scene); we modulate tempo by sentence length and pause density, not by voice parameters.

| Beat type | Target rate | How to achieve it |
|---|---|---|
| `hook` | faster — 2.6 w/s | Shorter sentences, no landings until the question lands. |
| `define` | baseline — 2.4 w/s | Default shape. |
| `motivate` | faster — 2.6 w/s | Question-mode; the energy is forward. |
| `example` | slower — 2.2 w/s | Landings after each computational step. |
| `generalize` | slower — 2.1 w/s | Landing on the named result; 0.8 s pause before, 0.8 s after. |
| `recap` | baseline — 2.4 w/s | Steady; closing beat should feel settled, not stretched. |

"Rate" here is a planning target. The script agent doesn't measure; it picks sentence length + pause density per the table, and rate falls out.

### 5. Pause placement heuristics (for the script agent)

Place a **landing pause** (0.8 s) after:

- A formal naming sentence: "That's the derivative." → pause.
- A punchline in a closing beat.
- The last sentence before a beat transition *if* the next beat opens with a contrasting idea.

Place a **micro-pause** (0.4 s) after:

- A sentence that sets up the next one ("Watch what happens.") → next sentence is the payoff.
- A long clause break that the comma isn't quite handling on its own.
- The final word of a computed intermediate result ("…so the slope is 2.") before moving to the next calculation.

Do **not** place a pause:

- Between every sentence (restores the reading-aloud cadence; strips the rhythm).
- Immediately before a signpost ("Watch.") — the signpost itself does the orienting.
- On the first word of a beat — the scene boundary's 1.5 s already cleared the air.

### 6. The sync agent's `wait_after_seconds`

`AnimationTiming.wait_after_seconds` is the time to hold on an animation's final frame before the next animation starts. It is separate from pauses in the narration.

Sync-side rule:

- If the animation's last word anchor is followed by an authored pause, set `wait_after_seconds = 0` — the authored pause already covers the hold.
- If the animation ends on a word that has no pause marker and the next animation is `run_after` this one, set `wait_after_seconds = 0.15 s` (a visual beat, not a listener-audible pause).
- At the last animation of a scene, set `wait_after_seconds = 0.3 s`. The 1.5 s scene-gap pause then trails this in the final cut.

### 7. Drift and the budget

Drift in `SyncPlan.drift_seconds` comes from cumulative mismatch between `duration_seconds` (Manim's wall-clock for an animation) and the word-interval the animation was anchored to. Target: < 0.15 s per marker, < 0.5 s accumulated per scene.

If accumulated drift exceeds budget, the Phase-1 play is:
1. Extend the final animation's `run_time` to absorb the overflow (if audio is longer than video).
2. Otherwise, append silence to the TTS audio to match the video length.
3. Do **not** rewrite the script to "fix" pacing — script is upstream.

Phase 2 flips this: the sync agent can request a scene regeneration with new animation `run_time`s.

## Examples

### Example 1 — 28 s beat with pauses marked

Narration tokens (from `spoken-narration-style` example 1):

```
["Watch", "what", "happens", "as", "we", "slide", "the", "two", "points", "together.",
 "The", "slope", "between", "them", "is", "easy.", "It's", "rise", "over", "run.",
 "As", "the", "points", "get", "close,", "the", "slope", "approaches", "a", "single", "number.",
 "At", "x", "equals", "one,", "that", "number", "is", "two.",
 "That", "number", "—", "the", "slope", "at", "a", "single", "instant", "—",
 "is", "the", "derivative."]
```

Authored pause markers:

- `ScriptMarker(word_index=9,  marker_type="pause", ref="micro")`    — micro after "together."
- `ScriptMarker(word_index=19, marker_type="pause", ref="micro")`    — micro after "run."
- `ScriptMarker(word_index=38, marker_type="pause", ref="landing")`  — landing after "two."
- `ScriptMarker(word_index=51, marker_type="pause", ref="landing")`  — landing after "derivative."

Budget: 2 micro (0.8 s total) + 2 landing (1.6 s total) = 2.4 s of authored silence in a ~28 s beat. In range. Last pause doubles as the pre-boundary settle; the sync agent will add the 1.5 s scene-gap *after* it.

### Example 2 — sync agent resolving drift

For the same beat, suppose Manim's animation timings sum to 11.8 s and the TTS audio (with silences) sums to 12.3 s. Drift = +0.5 s (audio longer). Phase 1 fix: extend the final animation's `wait_after_seconds` from 0.3 s to 0.8 s — absorbs the drift without re-rendering.

`SyncPlan.drift_seconds = 0.0` after the adjustment (drift was resolved by padding, not left in the plan).

### Example 3 — over-paused beat (what not to do)

Script agent produces a 30 s beat with 6 landings and 4 micros. Total authored silence: 6 × 0.8 + 4 × 0.4 = 6.4 s. Effective speaking time: 23.6 s at 2.4 w/s = ~57 words. The narration *sounds* like every sentence is the payload; the viewer stops distinguishing which ones actually are. Fix: keep at most 2 landings and at most 3 micros.

### Example 4 — zero-pause beat (the default failure)

First-draft scripts often have no pause markers at all. ElevenLabs still inserts ~50–300 ms on periods, so the audio isn't literally unbroken — but the *landings* don't land. The critic should flag "no landing pauses in a beat with a named concept" as a high-severity issue; the fix is to add one 0.8 s pause after the naming sentence.

## Gotchas / anti-patterns

- **Stacking sources.** Authored pause on a period + sync padding + TTS-natural pause = three gaps in a row. The coordination rule exists to prevent this; violate it and every landing feels like a skip.
- **Marking a pause at a scene boundary.** The sync agent already adds the 1.5 s gap. Authoring one there double-counts. Let scene-gap pauses live outside the script.
- **Continuous-valued pause lengths.** "0.6 s" or "1.1 s" are not options in Phase 1. Round to the nearest of {0.4, 0.8, 1.5}. The restriction simplifies both the rubric and the regression diff.
- **Treating TTS stability as a pacing knob.** Stability affects timbre consistency, not rate. If the narration feels fast, shorten sentences; if slow, tighten.
- **Pausing inside a sentence.** Commas belong to the sentence; the micro-pause belongs between sentences. Pauses mid-sentence (unless the sentence has an em-dash structure) make the narration sound stilted.
- **Padding silence to hit target duration.** If a beat is 4 s short of its storyboard target, the fix is narrative content, not trailing silence. Never pad with >1.5 s of silence.
- **Ignoring drift under 0.15 s.** It's within budget; leave it. Every correction has an error bar of its own, and chasing sub-budget drift introduces new error.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. Three pause lengths, per-beat budget, beat-type rate table, composition rule against ElevenLabs natural pauses, sync `wait_after_seconds` resolution. Paired with `spoken-narration-style` and Rule 4 of `pedagogy-cognitive-load`.
