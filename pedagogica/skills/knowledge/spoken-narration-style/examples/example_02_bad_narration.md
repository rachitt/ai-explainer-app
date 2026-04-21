# Example 02 — bad narration (same beat, negative example)

Same input prompt as `example_01_good_narration.md`. This is what a first draft often looks like when the agent hasn't loaded this skill. Used as a negative fixture for the critic.

---

## Narration (draft — do not ship)

So, what I'm going to try to show you in this next little bit is how, as we slide the two points along our parabola y equals x squared together, which we were looking at in the previous scene, the slope of the secant line between them, which is of course just rise over run, approaches a specific value — namely 2, at the particular point where x equals 1 — and this value is what we call the derivative of the function at that point, or f prime of x, though in this case we're evaluating it at x=1, so it's f prime of 1.

Maybe the best way to think about it is that the derivative could kind of be understood as being a slope, or at least that's one way of looking at what's happening here.

---

## Why this fails

- **Sentence shape**: two sentences, 88 and 27 words. First sentence has 5 subordinate clauses; violates cognitive-load Rule 3 and narration-style §1 hard.
- **Signposting**: preamble ("what I'm going to try to show you") burns the opening without orienting.
- **End-weight**: payload ("the derivative at 1 is 2") buried mid-sentence, surrounded by clarifying clauses.
- **Redundancy budget**: "f prime of x" and "derivative" both named in the same sentence with no pause between; the echo happens too fast to register.
- **Voice**: first-person singular ("I'm going to try to show you"), three hedges in the second sentence ("maybe", "could kind of be", "one way of looking").
- **Breath**: one period in the whole block. TTS will run out of air.
- **Notation leak**: "f prime of x" appears in spoken text adjacent to "f prime of 1"; the visual should carry these, not the narration.

---

## Expected critique output

When `pedagogical-critic` scores this against `pedagogical-critique` + this skill loaded, it should surface at minimum:

- `sentence_length_violation` on sentence 1 (88 words).
- `signpost_missing` at beat-open (preamble does not count).
- `end_weight_violation` on sentence 1 (payload mid-sentence).
- `hedge_overuse` on sentence 2.
- `voice_first_person_singular` on sentence 1.
- `breath_point_deficit` across the block.
