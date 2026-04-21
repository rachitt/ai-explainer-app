# Example 01 — good narration (derivative as slope, scene 2 of 5)

Input prompt to script agent (fixed, used for `test_skill_quality.py`):

> Scene 2 of an explainer on the derivative. Beat type: `define` via DMEG. Anchor: `y = x²`. Prior beat established the parabola and a secant between two points on it. This beat slides the points together and names the derivative. Target: 28 seconds, one new concept, at most 2 highlights on screen.

---

## Narration (text as it should appear in `Script.text`)

Watch what happens as we slide the two points together.

The slope between them is easy. It's rise over run.

As the points get close, the slope approaches a single number.

At x equals one, that number is two.

That number — the slope at a single instant — is the derivative.

---

## Properties

- 5 sentences, 42 words total.
- Longest sentence: 12 words.
- One orienting signpost ("Watch what happens"), one landing ("that's the derivative", echo-named).
- End-weight used in sentences 3, 4, and 5 (payload on the last word).
- Four period-bounded breath points; TTS will breathe at each.
- Zero LaTeX; zero first-person singular; zero hedging.
