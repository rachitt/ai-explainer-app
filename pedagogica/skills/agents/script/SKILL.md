---
name: script
version: 0.0.1
category: orchestration
triggers:
  - stage:script
requires: []
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

## Explain, don't recite

A script that reads the symbols on screen aloud is a script that teaches nothing. The narration has to explain **why** each piece is there, not just name it. This is the single biggest pedagogical failure mode.

**Recitation (bad):**
> "Degree three adds minus x cubed over six. Degree five adds x to the fifth over one hundred twenty."

**Explanation (good):**
> "The third term matches how the curve bends. Sine curves downward past zero, so we subtract a cubic. The fifth term matches how that bending turns around — the curve comes back up, so we add a smaller term, x to the fifth."

Concrete rules:

- **Every new symbol on screen earns one *because* sentence.** When a term, coefficient, or piece appears, the narrator names what it does and why — not what it says.
  - BAD: `"Add minus b times x dot."` (recitation)
  - GOOD: `"We add a drag force. It opposes motion, so it's negative. It's proportional to velocity, because faster motion hits more air."`
- **Name the role before the symbol.** "The restoring force — the thing that pulls the spring back" — *then* the symbol. The viewer needs the concept before the glyph.
- **When the equation has multiple terms, give each a short role name.** "Three parts: the inertia term, the damping term, the spring term. Sum them and the total is zero." The viewer hears *structure*, not *tokens*.
- **Reading a derivation out loud is not teaching.** If the narration says "multiply both sides by X, divide both sides by Y", the viewer has a watchable derivation — not an understandable idea. Rewrite: "We want a form where Y drops out, so we normalize."
- **Ask the viewer's question before answering it.** "Why that specific coefficient?" "What happens if we stop after one term?" "Does this work everywhere?" Posing the question primes the viewer to receive the answer. Answering unasked questions is noise.
- **Pass the sanity check.** Read the whole script aloud. If more than half the sentences could be deleted without changing what the viewer *understands* about the topic, the script is reciting, not explaining.

## Opening: ease the viewer in

A video is not a lecture notes dump. The first 5–10 seconds decide whether the viewer keeps watching.

**Hook-scene opening rules (scene_01):**

- **The opening must pose the storyboard hook question.** `scene_01` — or the dedicated hook beat if the storyboard has one — must pose `03_storyboard.json.hook_question` in the narration, either exactly or as a one-breath paraphrase. The answer must land by the end of the video's `generalize` or `recap` beat.
- **Open with a 2–5 word question or punchy phrase.** "Quick question." "Watch this." "Here's a puzzle." Read it aloud — if the first sentence takes more than ~2 seconds to say, shorten. Calibrated against Khan Academy's opening cadence.
- **Then set up a concrete demo with specific objects.** Baseballs, garden hose, swing, rubber band — not "a mass" or "a particle." Name the objects the viewer can picture.
- **Invite the viewer to predict.** "Which one hits the ground first? My intuition says…". Framing a prediction the viewer silently makes is the hook — they now have skin in the reveal.
- **Run the demo with action cues.** "Ready? Here goes." / "Let's see." / "Watch." / "Boom." The narrator is *performing*, not *describing*. Never use passive constructions ("a ball arcs through the air") in the hook.
- **Reveal the result, then create the mystery.** "Both hit at the same time. But why?" — the "but why?" carries the viewer into the define beat.
- **No jargon in the first sentence.** No `\rho`, no "cross-sectional area", no "restoring force". Those names arrive in scene_02 at the earliest.
- **Name the topic *after* the mystery.** Viewer should want the answer before hearing the formal name.

Concrete before/after:

```
BAD (bluntly technical):
  "Pull the mass to the right and let it go. It swings, and swings again,
   a little shorter each time. Something is eating the amplitude."
GOOD (familiar → narrow → question):
  "Push a kid on a swing. Let go. They swing back, and back again, but
   each swing is a little smaller. Eventually the swing stops. What is
   taking the energy out — and can we write down how fast it happens?"

BAD:
  "Here is the wide section, with cross-sectional area capital A one."
GOOD:
  "Turn on a garden hose. Pinch the end. The water shoots out faster. Why
   does the flow speed up the moment the opening gets smaller? The answer
   is simple, and it sits in two laws."
```

Concrete hook-question example:

- Intake `hook_question`: `"why does a phone charging from empty slow down near the end?"`
- `scene_01` first three sentences: `"Plug in an empty phone. Watch the number climb — fast at first, then slower, then crawling the last 5%. Why?"`

**Define-scene opening rules (scene_02, first "define" beat):**

- **Bridge in one half-sentence from the hook.** "Back to the swing" or "So — what is eating the amplitude". Never restart.
- **Introduce one symbol at a time, framed by its noun phrase.** "The force the spring pulls with, which we'll call the restoring force" — then *after* the viewer has the concept, write the symbol. Symbol follows noun, not the reverse.

**Later beats** may assume the hook has done its job — no re-warming. But every beat should begin with a phrase that tells the viewer *where we are in the argument*, not a cold equation.

**Anti-patterns** (see the Anti-patterns section below for the full list):

- Starting scene_01 with an imperative ("Pull the mass…", "Consider a wire…") — treats the viewer like a lab partner, not a curious person.
- Starting with the formal definition. Formal names belong after the motivation, not before.
- Starting with "In this video we will…" — classroom frame; 3blue1brown-style explainers don't announce themselves.

## Spoken-narration style (summary — see `spoken-narration-style` for the full rules)

### Cadence quotas (calibrated against Khan Academy 2026-04-23 benchmark)

Measured against a 686s Khan Academy AP Physics projectile lecture (Sal Khan's voice: 2.87 wps, 192 sentences, 86 first-person markers, 38 demo-action words, 53 questions). Hit these quotas to avoid sounding like textbook narration:

- **Short-sentence quota:** ≥ **25% of sentences ≤ 6 words.** Short lines carry rhythm. "Quick question." "But why?" "Let's see." "Here goes." "Both balls hit."
- **Rhetorical-question quota:** ≥ **1 question per 40 words.** Framed as "Why?" / "What does this mean?" / "Which one wins?" — drive the viewer forward.
- **First-person-plural quota:** ≥ **8 uses of "we" / "let's" / "we've" per 100 words.** Invites the viewer into the investigation. "We have a…", "Let's see what happens.", "We've now got…" Replace "the system is…" with "we've got a system…"
- **Demo-action vocabulary:** use "Ready?" / "Here goes." / "Boom." / "Watch." / "Notice." / "Look." — **at least 2 per scene**, one in the hook. These are the audible cues that the narrator is running an experiment, not describing one.
- **Sentences ≤ 15 words on average, hard cap 22.** Read it aloud; if it feels clotted, cut.
- **At most one subordinate clause per sentence.** Two is allowed only in short sentences (< 15 words). See `pedagogy-cognitive-load` Rule 3.
- **Say, don't show.** Do not describe what's on screen ("as you can see, the curve…"). The visual tier shows; narration says the idea.
- **Concrete nouns beat abstract nouns.** "The slope at x = 1 is 2" beats "the derivative's value at that point".
- **No throat-clearing.** Drop "so", "now let's", "basically", "essentially" at sentence starts unless they earn the beat.
- **Numbers in words for small integers** (`two`, `three`), digits for anything larger or any coefficient (`x = 1`, `f'(2) = 4`).
- **Never emit LaTeX or unicode math in `text`.** Say the math: `"f prime of x equals two x"`, not `"f'(x) = 2x"`. TTS garbles LaTeX.
- **Never bare a single Latin letter.** `"P is the static pressure"` → `"the static pressure term, capital P,"`. ElevenLabs reads a lone letter in mid-sentence as a noise or abbreviation and it clanks. Rule: every letter-variable ("v", "A", "P", "G", "h") must sit inside a noun phrase that introduces it ("the velocity v", "the area A one", "the gauge G two"). After the introduction, you may refer back using the same noun phrase, not the bare letter.
- **Greek letters: spell them the way you'd speak them.** Write `"rho"`, `"theta"`, `"phi"`, `"omega"`, `"pi"`, `"mu"`, `"sigma"`, `"epsilon"`. The TTS preprocessor respells `"rho"` → `"roe"` and similar at `pedagogica-tools elevenlabs-tts --pronounce` (default on); don't do the respelling yourself.
- **Subscripts and superscripts read by position.** `"v_1"` → `"v one"`, `"x^2"` → `"x squared"`, `"A^{(2)}"` → `"A to the two"`, `"f'"` → `"f prime"`. Never write `"v subscript one"` — too robotic.
- **Never narrate derivative operator names.** TTS says `"x double dot"` and `"x dot"` literally, and they sound like gibberish. Use the SEMANTIC name of the quantity instead:
  - `\ddot{x}` → `"the acceleration"` (or just `"acceleration"` after first mention)
  - `\dot{x}` → `"the velocity"` (or `"the rate of change of x"` when x is abstract, not a position)
  - `\frac{d}{dx}` → `"the derivative with respect to x"` or just `"the derivative"`
  - `\frac{dA}{dt}` → `"the rate of change of A"`
  - `f'(x)` → `"f prime of x"` (this one is conventional and fine)
  - `x'(t)` → `"the velocity"` (if x is position)
  - **Pair it with the visual.** When the EQUATION on screen shows `m\,\ddot{x} = -k\,x`, the narration says `"mass times acceleration equals minus k times x"`. The viewer sees the operator; the narrator names the concept.
- **Never dictate the equation form.** Don't read the LaTeX out loud. Don't say `"x dot dot plus two gamma x dot plus omega nought squared x equals zero"`. Say `"acceleration plus damping term plus restoring term equals zero"` or `"the equation has three parts: inertia, damping, and spring"`. The visual carries the symbols; narration carries the meaning.
- **Fractions spelled out.** `"1/2"` → `"one half"`, `"3/4"` → `"three quarters"`, `"1/n"` → `"one over n"`. Do not let digit-slash-digit through — TTS reads it as "one slash two".
- **Proper names with tricky phonetics.** `"Bernoulli"`, `"Euler"`, `"Cauchy"`, `"Laplace"`, `"Eigen-"`. The pronunciation preprocessor handles the common ones; prefer writing the correct spelling and trust the preprocessor over respelling inline.
- **Read the script aloud before emitting.** Listen for: back-to-back hard consonants, tongue-twister clusters, and any place where the audio would need to "spell" rather than "say". Rewrite those.

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
- Do **not** open scene_01 with an imperative or a formal definition. Open with a familiar phenomenon (see "Opening: ease the viewer in").
- Do **not** use technical terms before they are motivated. "The damping coefficient gamma" in sentence 1 lands as noise; motivate the concept first, name it second.
- Do **not** start a define scene with a cold equation. Bridge from the hook in one half-sentence, then introduce the symbol inside a noun phrase.
- Do **not** describe a scenario passively ("A ball arcs through the air…", "The mass oscillates…"). Narrator must *perform* the demo, not narrate it from outside. Use "we", "let's", "here goes", "watch".
- Do **not** ship a scene with zero short (≤6 word) sentences, zero questions, or zero first-person markers. Those three quotas are the KA benchmark floor (see Cadence quotas).
