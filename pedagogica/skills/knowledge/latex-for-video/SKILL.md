---
name: latex-for-video
version: 0.2.0
category: chalk
triggers:
  - stage:chalk-code
  - stage:chalk-repair
  - element_type:math
requires:
  - chalk-primitives@^0.1.0
token_estimate: 2800
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-22
description: >
  How to write LaTeX inside chalk scenes so equations read at video scale —
  scale tier conventions; composing equations out of multiple MathTex objects
  via next_to; \underbrace / \overbrace annotations; multi-line derivations;
  TransformMatchingTex for equation-edit animations. Loaded by chalk-code any
  time a scene contains math, and by chalk-repair on any LaTeX-classified
  error.
---

# latex-for-video

## Purpose

chalk renders LaTeX via `MathTex(tex_string, color=..., scale=...)`. That's not the skill — the skill is picking the *right* LaTeX for a 720p video where equations share the frame with a graph, and editing equations in a way the viewer's eye can follow.

Four craft problems keep showing up:

1. **Sizing.** The default LaTeX glyph size is wrong for most roles. Use the named scale tiers (`SCALE_DISPLAY` / `SCALE_BODY` / `SCALE_LABEL` / `SCALE_ANNOT`) from `chalk.style`.
2. **Colour-coded terms.** A viewer tracks a term through a transformation only if it's coloured distinctly. chalk's `MathTex` takes a *single* `tex_string` with no `mobj[i]` indexing — compose multi-colour equations by placing multiple `MathTex` objects side-by-side via `next_to`.
3. **`\underbrace` annotations.** Showing which piece of an equation *is* something. Two paths: inline LaTeX `\underbrace` (one mobject, all at once) vs chalk's `Brace` primitive (animated in as a separate beat).
4. **Morphing equations.** `TransformMatchingTex` tweens source→target by matching identical LaTeX tokens.

## When to load

- **chalk-code — any scene with math.** For calculus, every scene.
- **chalk-repair — on LaTeX-classified errors.** Most LaTeX errors are configuration (missing package) and live in `chalk-debugging`. Content errors — bad brace matching, raw `\color` inside MathTex, unescaped `%` — get fixed here.

## Core content

### 1. Scale tier conventions

chalk's `MathTex` takes `scale=` (a multiplier on a glyph baseline size), NOT `font_size`. Pick from the named tiers:

| Role | Tier | Scene behaviour |
|---|---|---|
| **Hero equation** (single focus, dominates frame) | `SCALE_DISPLAY` | The thing the scene is about. Occupies ZONE_CENTER. |
| **Running step / body equation** (derivation line, substituted form) | `SCALE_BODY` | Readable, doesn't compete with the hero. |
| **Object label** (variable name, axis label, point label) | `SCALE_LABEL` | Small enough to hug what it labels. |
| **Annotation / caption** (tiny remark, unit, legend) | `SCALE_ANNOT` | Legend-level; viewer isn't expected to read while narration runs. |

`SCALE_MIN = 0.40` is the floor. If a layout wants smaller text, the layout is wrong — drop an element, don't shrink.

**Rule of thumb.** If a size seems "between tiers", go *down*. In-between sizes read as "sort of important" and the viewer's eye doesn't know where to land.

**Never.** `MathTex(r"...", scale=0.37)` or any literal number — the chalk-lint rule **R2-magic-scale** trips on non-tier values. Update `style.py` if a new tier is genuinely needed.

### 2. Colour-coded terms (composition, not indexing)

chalk's `MathTex` is **one LaTeX string → one VGroup of glyphs**. There is no `eq[i]` substring accessor — the manim idiom `MathTex(r"\frac{d}{dx}", r"x^2", ...)[1].set_color(YELLOW)` crashes (see lint rule **R8-mathtex-variadic**).

Compose coloured terms by placing multiple `MathTex` objects with `next_to`:

```python
from chalk import MathTex, next_to, PRIMARY, YELLOW, BLUE, GREY, SCALE_BODY

# Build: d/dx ( x^2 + 3x ) = 2x + 3
# Each semantic piece is its own MathTex.
lhs   = MathTex(r"\frac{d}{dx}",     color=PRIMARY, scale=SCALE_BODY)
lp    = MathTex(r"(",                color=GREY,    scale=SCALE_BODY); next_to(lp,    lhs,  direction="RIGHT", buff=0.08)
t_sq  = MathTex(r"x^2",              color=YELLOW,  scale=SCALE_BODY); next_to(t_sq,  lp,   direction="RIGHT", buff=0.05)
plus1 = MathTex(r"+",                color=GREY,    scale=SCALE_BODY); next_to(plus1, t_sq, direction="RIGHT", buff=0.08)
t_3x  = MathTex(r"3x",               color=BLUE,    scale=SCALE_BODY); next_to(t_3x,  plus1, direction="RIGHT", buff=0.08)
rp    = MathTex(r")",                color=GREY,    scale=SCALE_BODY); next_to(rp,    t_3x, direction="RIGHT", buff=0.05)
eq    = MathTex(r"=",                color=GREY,    scale=SCALE_BODY); next_to(eq,    rp,   direction="RIGHT", buff=0.12)
r_2x  = MathTex(r"2x",               color=YELLOW,  scale=SCALE_BODY); next_to(r_2x,  eq,   direction="RIGHT", buff=0.08)
plus2 = MathTex(r"+",                color=GREY,    scale=SCALE_BODY); next_to(plus2, r_2x, direction="RIGHT", buff=0.08)
r_3   = MathTex(r"3",                color=BLUE,    scale=SCALE_BODY); next_to(r_3,   plus2, direction="RIGHT", buff=0.08)
```

Then `self.add(lhs, lp, t_sq, plus1, t_3x, rp, eq, r_2x, plus2, r_3)` and `self.play(FadeIn(lhs, run_time=0.4), ...)` etc.

**Consistency across a job.** Pick a palette role per variable and hold it:

| Colour | Role |
|---|---|
| `PRIMARY` | operators, LHS identifiers, "the thing" |
| `YELLOW` | payoff quantity, the hero term being transformed |
| `BLUE` | input variable, free parameter |
| `GREEN` | correct / target value |
| `GREY` | brackets, commas, equals — visual connectives |

See `chalk/CLAUDE.md` "Palette semantics" for hard rules (e.g., never `RED_FILL` on text).

### 3. `\underbrace` and `\overbrace` annotations

Use case: annotate a sub-expression as "this part is the derivative" or "this factor is small".

**Path A — inline LaTeX `\underbrace`** (one mobject, renders from frame 1):

```python
eq = MathTex(
    r"f'(x) = \underbrace{\lim_{h \to 0}}_{\text{limit}} "
    r"\underbrace{\frac{f(x+h) - f(x)}{h}}_{\text{difference quotient}}",
    color=PRIMARY, scale=SCALE_BODY,
)
```

Simple. Drawback: the underbrace is baked in — you can't reveal it as its own beat.

**Path B — chalk's `Brace` primitive** (animated in as a separate beat):

```python
from chalk import Brace, MathTex, Text, FadeIn, next_to, PRIMARY, GREY, SCALE_BODY, SCALE_ANNOT

eq = MathTex(r"f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}", color=PRIMARY, scale=SCALE_BODY)
self.add(eq)
self.play(FadeIn(eq, run_time=0.8))
self.wait(0.8)

# Brace under the difference-quotient half. Anchor by the whole eq mobject's right half
# via a dummy reference mobject, or use Brace(target_mob, direction="DOWN") if your
# chalk version supports it.
brace = Brace(eq, direction="DOWN", buff=0.12, color=GREY)
brace_lbl = Text("difference quotient", color=GREY, scale=SCALE_ANNOT)
next_to(brace_lbl, brace, direction="DOWN", buff=0.1)
self.add(brace, brace_lbl)
self.play(FadeIn(brace, run_time=0.4), FadeIn(brace_lbl, run_time=0.4))
```

More code, more control: the brace lands *after* the equation is read.

**Rule of thumb.** If the annotation is part of the mental model ("this factor is x"), use Path A — it shouldn't feel optional. If the annotation is a didactic callout ("notice this is the derivative definition"), use Path B — the appearance itself is the lesson.

### 4. Equation morphs with `TransformMatchingTex`

`TransformMatchingTex(src, tgt, run_time=1.5)` tweens source → target by matching identical LaTeX token sequences. Shared tokens Transform between positions; source-only tokens FadeOut; target-only tokens FadeIn.

```python
from chalk import MathTex, TransformMatchingTex, PRIMARY, SCALE_BODY

src = MathTex(r"\frac{d}{dx} x^2 = 2x",   color=PRIMARY, scale=SCALE_BODY)
tgt = MathTex(r"\frac{d}{dx} x^3 = 3x^2", color=PRIMARY, scale=SCALE_BODY)
self.add(src)
self.play(FadeIn(src, run_time=0.6))
self.wait(0.6)
self.play(TransformMatchingTex(src, tgt, run_time=1.5))
```

`\frac{d}{dx}` and `=` tokens anchor; `x^2` morphs toward `x^3`; `2x` morphs toward `3x^2`.

**chalk has no `key_map` override.** Manim's `key_map={r"x^2": r"x^3"}` override is NOT supported in chalk's `TransformMatchingTex`. If automatic matching picks the wrong pairing, split the equation into multiple `MathTex` objects composed via `next_to` (§2 above) and animate the changing piece with a plain `Transform` or `FadeOut`+`FadeIn`.

**Gotcha.** Identical source and target → no animation. Use a direct `FadeIn` on new content instead of `TransformMatchingTex` if the transform is a no-op.

### 5. Multi-line derivations

For a step-by-step derivation, write each line as its own `MathTex` stacked via `next_to(line_i, line_i-1, direction="DOWN", buff=0.3)`:

```python
from chalk import MathTex, FadeIn, next_to, PRIMARY, SCALE_BODY

l1 = MathTex(r"(x+1)^2 = (x+1)(x+1)",     color=PRIMARY, scale=SCALE_BODY)
l2 = MathTex(r"\;= x^2 + x + x + 1",      color=PRIMARY, scale=SCALE_BODY); next_to(l2, l1, direction="DOWN", buff=0.3)
l3 = MathTex(r"\;= x^2 + 2x + 1",         color=PRIMARY, scale=SCALE_BODY); next_to(l3, l2, direction="DOWN", buff=0.3)

self.add(l1); self.play(FadeIn(l1, run_time=0.6)); self.wait(0.5)
self.add(l2); self.play(FadeIn(l2, run_time=0.6)); self.wait(0.5)
self.add(l3); self.play(FadeIn(l3, run_time=0.6)); self.wait(1.2)
```

Anchor the first line near the top of the zone so later lines flow *down* rather than pushing earlier lines off-frame.

**Don't** try `TransformMatchingTex` between a partial derivation and the full one — the partial has different glyph coverage; matching gets confused. Reveal line-by-line with `FadeIn`.

### 6. The LaTeX install

chalk calls out to `pdflatex` (or `latex`) + `dvisvgm` behind the scenes for `MathTex` / `Text`. Phase 1 packages:

- `standalone` (document class).
- `preview` (dependency).
- `doublestroke` (for `\mathbb`).
- `relsize` (relative sizing commands).
- `everysel`, `ms`, `rsfs`, `setspace`, `tipa`, `wasy`, `wasysym`, `xcolor`, `jknapltx` (transitive deps).

macOS install:

```
brew install --cask basictex
eval "$(/usr/libexec/path_helper)"
sudo tlmgr update --self
sudo tlmgr install standalone preview doublestroke relsize everysel ms \
    rsfs setspace tipa wasy wasysym xcolor jknapltx
```

If `chalk-render` fails with `LaTeX Error: File 'XXX.sty' not found`, run `sudo tlmgr install <package-containing-XXX>`. The ten most common missing-package errors and exact `tlmgr` fixes are in `chalk-debugging`'s error catalog.

`pedagogica-tools chalk-render` injects `/Library/TeX/texbin` into the subprocess PATH (see `workflows/lessons.md` 2026-04-21 entry). Contributors on fresh macOS boxes still need basictex + the tlmgr packages above.

## Gotchas / anti-patterns

- **Forgetting `r"..."` raw strings.** `"\\frac"` works, `"\frac"` produces `\x0crac`. Always raw.
- **`MathTex` with multiple positional strings.** `MathTex(r"\sin", r"(", r"x^2", ...)` → `TypeError: got multiple values for argument 'color'`. chalk takes one `tex_string`. Enforced by **R8-mathtex-variadic**.
- **`\color{}` inside the LaTeX string.** Crashes chalk's LaTeX pipeline. Pass `color=` as a kwarg to `MathTex` instead.
- **`.set_color()` method call.** chalk has no `set_color` method on MathTex. Set colour at construction.
- **`Write(eq)` animation.** chalk has no `Write` — use `FadeIn(eq, run_time=0.6)`.
- **`mob[i]` substring indexing.** Crashes at runtime. Compose equations from multiple `MathTex` objects (§2).
- **`.scale(1.5)` on MathTex after construction.** Works but thickens glyph strokes unpleasantly. Build with the right `scale=SCALE_*` from the start; reserve runtime `.scale()` for short emphasis beats (1.1×–1.2×, then back).
- **Identical source and target to `TransformMatchingTex`.** No animation. Use `FadeIn` on new content.
- **`key_map=` argument.** Not supported — see §4. Split the equation into composable `MathTex` pieces.

## Changelog

- **0.2.0** (2026-04-22) — rewrote body for chalk. Dropped manim-specific API (indexed substrings, `font_size`, `Write`, `GrowFromCenter`, `key_map`). Added composition-via-next_to pattern for coloured terms, chalk-specific anti-patterns (R8 / no `\color`), chalk `Brace` primitive reference, chalk `TransformMatchingTex` without `key_map`. Requires updated from `manim-primitives` + `color-and-typography` to `chalk-primitives` only.
- **0.1.0** (2026-04-21) — initial ship (manim-native; deprecated).
