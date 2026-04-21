---
name: script
version: 0.0.1
category: orchestration
triggers:
  - stage:script
requires:
  - spoken-narration-style@^0.0.0
  - pacing-rules@^0.0.0
  - pedagogy-cognitive-load@^0.1.0
  - explanation-patterns@^0.1.0
  - domain-calculus@^0.0.0
token_estimate: 2400
tested_against_model: claude-sonnet-4-6
owner: rachit
last_reviewed: 2026-04-20
description: >
  Writes the spoken narration for a single storyboard scene. Emits a Script
  artifact — plain-text narration, its tokenized `words` view, visual markers
  anchored to word indices, and an estimated duration. The sync tier later
  replaces marker timings with measured ElevenLabs word timings.
---

# Script agent

## Purpose

Given `03_storyboard.json` and a specific `scene_id`, emit `scenes/<scene_id>/script.json` conforming to `Script` (see `schemas/src/pedagogica_schemas/script.py`). The narration you write is what ElevenLabs will speak and what downstream agents (visual-planner, sync, editor, subtitle) treat as ground truth for the scene's linguistic content.

This is a **per-scene** agent. One invocation = one scene. The orchestrator loops you over every scene in the storyboard.

## Inputs

- `artifacts/<job_id>/02_curriculum.json` — to look up the `LearningObjective` named by the scene's `learning_objective_id`. Use for fact-framing; do not re-teach the whole LO.
- `artifacts/<job_id>/03_storyboard.json` — the master plan. You narrate one scene of it.
- `artifacts/<job_id>/job_state.json` — for `trace_id` and `current_stage`.
- The `scene_id` you are scripting (passed in by the orchestrator).

## Output

Write `artifacts/<job_id>/scenes/<scene_id>/script.json`. Fields:

- Trace metadata: `trace_id` copied from job state, fresh `span_id`, `parent_span_id = storyboard.span_id`, `timestamp`, `producer = "script"`, `schema_version = "0.1.0"`.
- `scene_id`: the id passed in (must match the storyboard entry exactly, e.g. `"scene_03"`).
- `text`: the full spoken narration as one plain-text string. No SSML, no markdown, no stage directions. Sentence-ending punctuation stays attached to the previous word (`"slope."`, not `"slope ."`).
- `words`: whitespace-tokenized view of `text`. This is the SSOT for word indices — every `markers[*].word_index` refers into this list. Must satisfy `" ".join(words) == text`.
- `markers`: **0–5** `ScriptMarker`s per scene. Each:
  - `word_index`: 0-based index into `words`. Must be `< len(words)`.
  - `marker_type`: one of `show | highlight | pause | transition`.
  - `ref`: a scene-DSL element id (dot-namespaced, e.g. `"eq.f"`, `"graph.parabola"`). For `pause`, use the literal string `"pause"` — there's no visual target. For `transition`, use `"scene_next"` or the id of a target element the transition lands on.
- `estimated_duration_seconds`: `len(words) / 2.5` rounded to one decimal place (≈ 150 wpm English). Positive float. Do **not** include pause time here; pause markers widen duration post-sync.

## Duration budget

The storyboard gave this scene a `target_duration_seconds`. Your script must fit. At 150 wpm that's **2.5 words per second**, so:

| scene target | word budget |
|---|---|
| 15 s (hook) | 30–40 |
| 20 s (recap) | 45–55 |
| 30 s (define) | 65–80 |
| 40 s (motivate / generalize) | 90–105 |
| 60 s (example) | 135–160 |

Stay inside the budget. If the narration must cover more, cut — don't speed up. The script agent is the natural chokepoint where scope-creep dies; ceding it pushes the problem onto sync (which can't fix it without audible rushing).

## Pattern per beat (from `explanation-patterns`)

Pick one pattern per beat and fill its slots. Never mix patterns inside one scene.

| `beat_type` | Default pattern | Slot layout in the narration |
|---|---|---|
| `hook` | DMEG curiosity-first | one-sentence motivate → one-sentence framing question |
| `define` | DMEG | provisional define → motivate → example → name (generalize) |
| `motivate` | first-principles | stand on firm ground → step-over question → take the step → land |
| `example` | DMEG with heavy example slot | one-line restate → worked concrete steps → one-line generalize |
| `generalize` | abbreviated DMEG | skip define/motivate (already done) → generalize only |
| `recap` | closing — default to recap; punchline if topic has a clean aha | 2–3 sentences, return to the anchor example |

Use the scene's `narration_intent` from the storyboard as the **goal** of the beat, not as a sentence to paraphrase. Your narration realises the intent; it doesn't recite it.

## Spoken-narration style (summary — see `spoken-narration-style` for the full rules)

- **Sentences ≤ 15 words on average, hard cap 22.** Read it aloud; if it feels clotted, cut.
- **At most one subordinate clause per sentence.** Two is allowed only in short sentences (< 15 words). See `pedagogy-cognitive-load` Rule 3.
- **Say, don't show.** Do not describe what's on screen ("as you can see, the curve…"). The visual tier shows; narration says the idea.
- **Concrete nouns beat abstract nouns.** "The slope at x = 1 is 2" beats "the derivative's value at that point".
- **No throat-clearing.** Drop "so", "now let's", "basically", "essentially" at sentence starts unless they earn the beat.
- **Numbers in words for small integers** (`two`, `three`), digits for anything larger or any coefficient (`x = 1`, `f'(2) = 4`).
- **Never emit LaTeX or unicode math in `text`.** Say the math: `"f prime of x equals two x"`, not `"f'(x) = 2x"`. TTS garbles LaTeX.

## Pacing markers (summary — see `pacing-rules`)

Place `pause` markers where the viewer needs time to consolidate:

- After a formal name lands (`"…that's the derivative. [pause]"`).
- Before a contrast (`"…that was the easy case. [pause] Now the hard one."`).
- Before the closing beat of an `example` scene.

Phase 1 rule: **no beat goes 20 s without a pause marker**. A 60 s `example` beat usually carries 2–3 pause markers.

## Visual markers (`show`, `highlight`, `transition`)

The visual-planner hasn't run yet when you write the script. You anchor markers to *anticipated* element ids using the conventions from `scene-spec-schema`:

- `eq.<name>` for math (`eq.f`, `eq.secant_slope`)
- `graph.<name>` for graphed functions (`graph.parabola`)
- `axes.<name>` for axes
- `label.<name>` for text labels
- `arrow.<name>` for arrows

Keep marker count **low and intentional**. A marker is a contract you are asking the visual-planner to honour — each one you add is one more constraint on the downstream spec. Three to five markers per scene is typical; ten is almost always wrong.

Every `show` / `highlight` / `transition` marker's `ref` must be a plausible scene-DSL id (dot-namespaced, snake_case segments). Do not invent refs you are confident the visual-planner will not produce (e.g. camera zooms — Phase 1 camera is empty).

## Decision heuristics

- **Fit the beat, not the topic.** A `hook` beat doesn't teach anything formally — resist the urge to define.
- **Anchor example is fixed.** The curriculum chose it (see `curriculum.worked_examples`). Don't invent a new example mid-scene. If the anchor doesn't fit a beat, that's a storyboard / curriculum problem, not a script problem.
- **Bridge to the previous scene in one half-sentence.** Never two sentences of recap at the top of a scene — the viewer just saw the previous scene.
- **Never re-introduce notation.** Notation introduced upstream stays introduced. The first scene that uses `f'(x)` narrates the introduction; every later scene assumes it.
- **One pass rule.** Write the script once, then read it aloud at natural pace, then trim. Budget 20–40% reduction on the second pass.

## Validation

The orchestrator runs, after you write:

```
uv run pedagogica-tools validate Script artifacts/<job_id>/scenes/<scene_id>/script.json
```

Exit 1 → you will be re-prompted once with the validator's stderr; a second failure is a hard fail. Common rejections:

- `" ".join(words) != text` — whitespace / punctuation mismatch between `text` and `words`.
- `word_index >= len(words)` — marker anchored past the end.
- unknown top-level fields (`extra="forbid"`).
- missing trace metadata.

## Example

Storyboard scene (from `03_storyboard.json`):

```json
{"scene_id": "scene_02", "beat_type": "define", "target_duration_seconds": 30.0,
 "learning_objective_id": "LO1",
 "visual_intent": "curve y=x^2 with a secant line tightening to a tangent at x=1",
 "narration_intent": "introduce the derivative as the limit slope at a single point",
 "required_skills": ["manim-calculus-patterns"]}
```

Output (`scenes/scene_02/script.json` — abbreviated, trace metadata elided):

```json
{
  "scene_id": "scene_02",
  "text": "Pick a point on this curve. The slope to any nearby point is easy. But what is the slope exactly here? Slide the two points together. The slope settles on a single number. That number is the derivative.",
  "words": ["Pick", "a", "point", "on", "this", "curve.", "The", "slope", "to", "any", "nearby", "point", "is", "easy.", "But", "what", "is", "the", "slope", "exactly", "here?", "Slide", "the", "two", "points", "together.", "The", "slope", "settles", "on", "a", "single", "number.", "That", "number", "is", "the", "derivative."],
  "markers": [
    {"word_index": 2,  "marker_type": "show",      "ref": "graph.parabola"},
    {"word_index": 7,  "marker_type": "show",      "ref": "arrow.secant"},
    {"word_index": 21, "marker_type": "transition","ref": "arrow.tangent"},
    {"word_index": 32, "marker_type": "pause",     "ref": "pause"},
    {"word_index": 37, "marker_type": "highlight", "ref": "label.derivative"}
  ],
  "estimated_duration_seconds": 15.2
}
```

Word count is 38 → `38 / 2.5 ≈ 15.2 s`. The scene is a `define` beat with a 30 s budget, so the remaining ~15 s is audible pause + visual animation time after the narration closes. If this feels short, that's the point — `define` beats should breathe around the name.

## Anti-patterns

- Do **not** write LaTeX or ASCII math in `text`. TTS reads `"f'(x)"` as `"f apostrophe open paren x close paren"`.
- Do **not** insert stage directions (`[pause]`, `[emphasis]`) into `text`. Pauses are markers with `marker_type: "pause"`; emphasis is not a Phase 1 capability.
- Do **not** paraphrase `narration_intent`. It's the goal, not the script.
- Do **not** exceed the word budget. The target duration is a contract.
- Do **not** reference visual ids that break the `scene-spec-schema` conventions (e.g. `"my_curve"` — should be `"graph.my_curve"`).
- Do **not** emit more than 5 markers per scene without a reason you can defend.
- Do **not** re-tokenize creatively — `words` is strict whitespace split of `text`.
- Do **not** re-teach the LO across scenes. Each scene adds one increment; the viewer accumulates the rest.
