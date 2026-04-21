---
name: color-and-typography
version: 0.1.0
category: manim
triggers:
  - stage:visual-planner
  - stage:manim-code
requires: []
token_estimate: 1600
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Phase-1 fixed preset for palette, semantic colors, and typography in Pedagogica
  videos. One palette, one font stack, one set of type sizes — meant to ship
  calculus content at 720p. Brand-kit overrides are a Phase-4 concern; this skill
  is deliberately non-configurable. Used by the visual planner (when picking
  colors for elements) and the Manim code agent (when emitting color constants
  and font-size arguments).
---

# color-and-typography

## Purpose

Two agents decide how a Pedagogica video *looks*: the visual planner chooses semantic colours per element, and the Manim-code agent emits concrete hex/RGB and font arguments. If these two disagree on the palette, videos drift away from a recognisable visual identity. This skill is the single fixed preset they both load.

Phase 1 is not the time for brand kits. One preset, applied consistently, makes the regression suite a meaningful signal and leaves the brand-kit surface area for Phase 4 when it's a product feature.

## When to load

- Visual planner — **always**, so `SceneElement.properties.color` uses the semantic names in this skill.
- Manim-code agent — **always**, so the emitted Python resolves those names to the correct hex constants.
- Script / sync / editor — not needed.
- Do not load this skill expecting knobs. There are none in Phase 1.

## Core content

### Background

The video renders against a near-black background. Semi-dark rather than pure black so that anti-aliased edges don't punch out against the frame.

```
background = #0E1116
```

### Palette (hex + Manim name)

| Role | Hex | Manim constant (0.19.x) |
|---|---|---|
| `background` | `#0E1116` | custom (`ManimColor("#0E1116")`) |
| `primary` | `#E8EAED` | custom (near-white, warmer than `WHITE`) |
| `accent_blue` | `#4FC3F7` | close to `BLUE_D` — use the hex to guarantee match |
| `accent_yellow` | `#FFD54F` | close to `YELLOW_D` — use the hex |
| `accent_red` | `#EF5350` | close to `RED_D` — use the hex |
| `accent_green` | `#66BB6A` | close to `GREEN_D` — use the hex |
| `muted_grey` | `#9AA0A6` | custom |

Prefer the hex constants over Manim's built-in named colours. Manim's `BLUE` vs `BLUE_D` vs `BLUE_E` choice has bitten prior projects when defaults shift between versions; locking to hex removes the ambiguity.

### Semantic colours

These are the only semantic slots a scene element should ask for:

| Semantic name | Use for | Palette mapping |
|---|---|---|
| `primary` | Main math, primary text, the thing you're looking at | `#E8EAED` |
| `variable` | Free variables, input quantities, moving things | `accent_blue` |
| `result` | Output values, quantities being computed toward, punchline numbers | `accent_yellow` |
| `correct` / `limit_target` | The value being approached; a "yes, this" confirmation | `accent_green` |
| `error` / `bad_path` | A wrong answer being contrasted; a "not this" | `accent_red` |
| `annotation` | Axes labels, tick text, neutral captions | `muted_grey` |

The visual planner names the semantic slot; the Manim codegen looks it up in this table. Don't let scene specs contain raw hex — all the indirection is there to let Phase 4 swap the mapping without touching individual scenes.

### Colour use rules

- **One semantic role per element per scene.** An element tagged `variable` stays `variable` for the whole scene. If the narrative needs to reclassify it mid-scene, fade it out and re-introduce a new element.
- **Green means "correct" or "target"; red means "wrong" or "error."** Never invert. These map to cultural expectations; inverting them confuses even when the legend is explicit.
- **No more than four semantic slots active in one scene.** Above that, the colour key becomes the cognitive load. Pick the three or four that carry the beat.
- **Rainbow-every-term is forbidden.** Tagging each operand of a long expression with a different colour looks instructive in a still frame and reads as noise in motion.
- **Gradient backgrounds, textured fills, drop shadows — no.** Phase-1 aesthetic is flat, readable, legible-at-720p. Effects come later if at all.

### Typography

Two font families. Both must be available in the render environment; the Manim sandbox profile ensures this.

| Use | Family | Notes |
|---|---|---|
| Math (LaTeX) | Computer Modern (LaTeX default) | `MathTex` and `Tex` in Manim render with CM by default; don't override. |
| Chrome (titles, labels, annotations) | Inter | Weight 400 for body, 600 for titles. `Text(..., font="Inter")`. |

Fallbacks: if Inter is unavailable (shouldn't happen in the sandbox, but just in case), use `Helvetica` → `sans-serif`.

### Type sizes at 720p

`SceneElement.properties.font_size` is in Manim units; the numbers below are what maps to the pixel heights at 720p.

| Role | Manim `font_size` | Approx rendered height |
|---|---|---|
| Display math (the main equation of a beat) | `48` | ~56 px |
| Body math (secondary equations, in-frame substitutions) | `36` | ~42 px |
| Labels on objects (point labels, axis labels) | `28` | ~33 px |
| Annotations / captions | `22` | ~26 px |
| **Minimum** (the floor below which text becomes hard to read at 720p) | `20` | ~23 px |

Do not emit text below the minimum. If a layout seems to require smaller text, the layout is wrong — either the element is redundant (drop it) or the camera should be closer in a later phase.

### Contrast

All text must clear WCAG AA-large (7:1) against the background. With `#0E1116` background:

- `primary` (`#E8EAED`) — ~17:1 ✓
- `accent_blue` (`#4FC3F7`) — ~9.7:1 ✓
- `accent_yellow` (`#FFD54F`) — ~14:1 ✓
- `accent_green` (`#66BB6A`) — ~7.4:1 ✓
- `accent_red` (`#EF5350`) — ~5.8:1 **only use `accent_red` on fills or strokes ≥ 2 px, not on body text**
- `muted_grey` (`#9AA0A6`) — ~7.1:1 ✓ (borderline; annotation-only, not for main content)

`accent_red` is the only palette colour that doesn't clear AA-large as text. The restriction above is load-bearing.

## Examples

### Example 1 — scene element colouring (visual-planner output)

```json
{
  "elements": [
    {"id": "eq.f",       "type": "math",  "content": "f(x) = x^2",          "properties": {"color": "primary",    "font_size": 48}},
    {"id": "label.x",    "type": "label", "content": "x",                   "properties": {"color": "variable",   "font_size": 28}},
    {"id": "label.slope","type": "label", "content": "slope = 2x",          "properties": {"color": "result",     "font_size": 36}},
    {"id": "axes.main",  "type": "axes",  "content": "",                    "properties": {"color": "annotation"}}
  ]
}
```

### Example 2 — Manim codegen for the same (snippet)

```python
BG       = ManimColor("#0E1116")
PRIMARY  = ManimColor("#E8EAED")
VARIABLE = ManimColor("#4FC3F7")
RESULT   = ManimColor("#FFD54F")
ANNOT    = ManimColor("#9AA0A6")

self.camera.background_color = BG

eq_f = MathTex("f(x) = x^2", font_size=48).set_color(PRIMARY)
label_x = Text("x", font="Inter", font_size=28).set_color(VARIABLE)
label_slope = MathTex("\\text{slope} = 2x", font_size=36).set_color(RESULT)
axes = Axes().set_color(ANNOT)
```

Note: the codegen resolves semantic names to hex once at the top of the scene file; downstream `set_color` calls use the named constants.

### Example 3 — contrast-failing layout (what not to do)

```json
{"id": "caption.note", "type": "text", "content": "this is a side note", "properties": {"color": "error", "font_size": 22}}
```

`accent_red` body text at size 22 fails contrast. Fix: use `muted_grey` for neutral captions; reserve `accent_red` for the wrong-answer role, and when you do use it, put it on a fill or a stroke, not small body text.

## Gotchas / anti-patterns

- **Hard-coding hex in scene specs.** Use semantic names; the mapping lives here. Phase 4 brand-kit swap depends on this indirection.
- **Inventing new semantic slots.** If a scene wants "hypothesis yellow" distinct from `result`, resist. Either reuse `result`, or tag it `primary` with `stroke=dashed`. New slots require this skill to version-bump.
- **Using built-in Manim color names (`BLUE`, `GREEN`) directly.** They drift between versions. Route through the hex constants at the top of the codegen.
- **Text below 20 pt at 720p.** The floor is hard. Legibility is non-negotiable.
- **Red on text smaller than the display-math size.** Contrast floor; either larger, a fill, or pick a different slot.
- **Animating colour from one semantic slot to another mid-scene.** Breaks the "one role per element" rule; viewers track role by colour.
- **More than four active semantic slots in one scene.** Past that, the colour key is the thing being learned.

## Changelog

- **0.1.0** (2026-04-20) — initial Phase 1 ship. One palette, two fonts, five type sizes, explicit contrast table. Brand-kit hook (Phase 4) will override the hex table without changing scene specs.
