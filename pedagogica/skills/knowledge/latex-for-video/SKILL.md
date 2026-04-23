---
name: latex-for-video
version: 0.1.0
category: chalk
triggers:
  - stage:chalk-code
  - stage:chalk-repair
  - element_type:math
requires:
  - chalk-primitives@^0.1.0
token_estimate: 3800
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-21
description: >
  How to write LaTeX inside Manim scenes so equations read at video scale —
  font-size and scale conventions; indexed substrings and colour coding that
  survive a transform; \underbrace and \overbrace for annotated steps;
  aligned multi-line derivations morphed with TransformMatchingTex. Loaded by
  the Manim-code agent any time a scene contains math, and by Manim-repair
  on any LaTeX-classified error.
---

# latex-for-video

## Purpose

Manim can render any valid LaTeX. That's not the skill — the skill is picking the *right* LaTeX for a 720p video where equations share the frame with a graph, and editing equations in a way the viewer's eye can follow.

Four craft problems keep showing up:

1. **Sizing.** Default LaTeX at Manim's default `font_size=48` is slightly too big for an equation that shares the frame with a graph, and way too small for a hero equation. Use explicit size conventions.
2. **Colour-coded terms.** A viewer can read a three-term sum and track one term through a transformation *only* if that term is coloured distinctly. Indexed substrings are how you do this reliably.
3. **`\underbrace` annotations.** Showing which piece of an equation *is* something ("this part is the derivative"). Manim handles `\underbrace` natively, but the animation needs care.
4. **Aligned transformations.** Morphing `(x+1)^2` → `x^2 + 2x + 1` so shared parts sit still and only the change moves. `TransformMatchingTex` carries this, but only if the substrings are indexed consistently.

## When to load

- **Manim-code — any scene with math.** Which for calculus is every scene.
- **Manim-repair — on LaTeX-classified errors.** Most LaTeX errors are configuration (missing package) and live in `manim-debugging`. The ones that are *content* errors — ambiguous bracing, bad substring indexing — get fixed here.
- **Visual planner — no.** The planner decides *that* math appears, not *how* it's rendered.

## Core content

### 1. Font size conventions

Manim's `font_size` arg to `MathTex` / `Tex` sets the LaTeX point size in scene units. At 720p:

| Role | `font_size` | Scene behaviour |
|---|---|---|
| **Hero equation** (single-focus, dominates frame) | `72` | The thing the scene is about. Occupies the CENTER zone. |
| **Running step / annotation** (under a graph, beside an axis) | `36` | Readable, doesn't compete with the visual. |
| **Graph / axis label** (curve name, axis tick labels) | `28`–`32` | Small enough to sit near what it labels without dominating it. |
| **Inline caption** (micro-label in a corner) | `24` | Legend-level; viewer isn't expected to read while narration runs. |

**Rule of thumb**: if you find yourself wanting a `font_size` between tier values (e.g., 42), go *down*. The in-between sizes read as "this is sort of important" and the viewer's eye doesn't know where to land.

**Scaling vs font_size.** `MathTex(..., font_size=72)` is preferred over `MathTex(...).scale(1.5)`. `scale` scales the whole mobject including stroke widths; LaTeX glyph strokes at 1.5× scale get unpleasantly thick. Use `font_size` to size, `scale` only for temporary emphasis beats (scale up 1.2× during a "behold" moment, then back to 1.0×).

### 2. Indexed substrings

Passing a list of strings to `MathTex` makes each one an indexable sub-mobject:

```python
eq = MathTex(r"\frac{d}{dx}", r"\left(", r"x^2", r"+", r"3x", r"\right)",
             r"=", r"2x", r"+", r"3", font_size=60)
eq[2].set_color(YELLOW)   # "x^2" in yellow
eq[4].set_color(BLUE)     # "3x" in blue
```

Why index the `\left(`, `\right)`, `=` as their own entries: so a later `TransformMatchingTex` can match them as anchors — they stay put while `x^2` morphs into `x^3`.

**Indexing rules:**
- Each substring must compile as a LaTeX fragment on its own. A stray `\frac{d}{dx}` without its argument compiles fine (Manim wraps each one), but `\left(` alone does not — you need `r"\left("` and `r"\right)"` as *separate* strings (Manim handles the unmatched `\left`/`\right` specially in `MathTex`).
- For operators like `=`, `+`, `-`, always make them standalone substrings. Colour them `GRAY` to de-emphasize.
- Never break a single token: `r"\frac"`, `r"{d}"`, `r"{dx}"` as separate strings will compile but won't index the way you expect — `\frac` needs its two args inside the *same* string.

**Colour by semantic role:**

```python
CURVE_COLOR   = BLUE
VARIABLE      = YELLOW
PARAMETER     = GREEN
DERIVATIVE    = RED
```

Hold these consistent across scenes in a job. `color-and-typography` has the full palette.

### 3. `\underbrace` and `\overbrace` annotations

Use case: in the equation `f'(x) = lim_{h→0} (f(x+h) - f(x))/h`, you want to annotate `(f(x+h) - f(x))/h` as "difference quotient" and `h → 0` as "limit direction".

Two implementation paths, with different trade-offs:

**Path A — LaTeX-native `\underbrace`:**

```python
eq = MathTex(
    r"f'(x) = \underbrace{\lim_{h \to 0}}_{\text{limit}}"
    r"\underbrace{\frac{f(x+h) - f(x)}{h}}_{\text{difference quotient}}",
    font_size=56,
)
```

Simple, cheap to render. Drawback: the whole equation is one mobject, so you can't animate the underbrace in separately after the equation appears — it's there from frame 1.

**Path B — Manim's `Brace` + label (preferred for stepped reveals):**

```python
eq = MathTex(r"f'(x)", r"=", r"\lim_{h \to 0}", r"\frac{f(x+h) - f(x)}{h}", font_size=60)
self.play(Write(eq))
brace = Brace(eq[3], DOWN, buff=0.1)
brace_label = Text("difference quotient", font_size=28).next_to(brace, DOWN, buff=0.1)
self.play(GrowFromCenter(brace), Write(brace_label))
```

More code, more control: the brace can come in after the equation has been read, then fade out when the annotation has landed. Use this when the annotation is *pedagogically* separate from the equation — the viewer reads the equation, then the narrator says "notice this is just …" and the brace appears.

**Rule of thumb**: if the annotation is part of the mental model ("this factor is `x`"), use Path A — it shouldn't feel optional. If the annotation is a didactic callout ("notice that this is the derivative definition"), use Path B — the appearance itself is the lesson.

### 4. Aligned transformations

The cleanest equation-edit animation is one where shared substrings don't move. `TransformMatchingTex` does this by default, matching substrings by their rendered TeX string.

**Canonical use — reveal a simplification:**

```python
src = MathTex(r"\frac{d}{dx}", r"(", r"3x^2", r")", font_size=60)
tgt = MathTex(r"\frac{d}{dx}", r"(", r"3x^2", r")", r"=", r"6x", font_size=60)
self.play(Write(src))
self.play(TransformMatchingTex(src, tgt))
```

The `\frac{d}{dx}`, `(`, `3x^2`, `)` parts stay put; `= 6x` appears.

**Canonical use — replace a term:**

```python
src = MathTex(r"\frac{d}{dx}", r"x^2", r"=", r"2x", font_size=60)
tgt = MathTex(r"\frac{d}{dx}", r"x^3", r"=", r"3x^2", font_size=60)
self.play(TransformMatchingTex(src, tgt))
```

`\frac{d}{dx}` and `=` anchor; `x^2` morphs to `x^3`, `2x` morphs to `3x^2`.

**Gotcha: matching by string can surprise you.** `MathTex(r"2x")` and `MathTex(r"2", "x")` both produce a mobject with `2x` written on screen, but `TransformMatchingTex` treats them differently — the first has one substring `"2x"`, the second has two substrings `"2"` and `"x"`. If a transform looks right in one direction but weird in the other, mismatched indexing is almost always why.

**Fix when TransformMatchingTex is surprising:** Use `key_map` to make the match explicit.

```python
TransformMatchingTex(src, tgt, key_map={r"x^2": r"x^3", r"2x": r"3x^2"})
```

### 5. Multi-line derivations with `align`

For a step-by-step derivation, use `MathTex` with LaTeX `aligned` environment and step in new lines via `add_line_to`:

```python
derivation = MathTex(
    r"(x+1)^2 &= (x+1)(x+1) \\",
    r"        &= x^2 + x + x + 1 \\",
    r"        &= x^2 + 2x + 1",
    font_size=48,
)
```

Each line is one substring; `Write(derivation[0])`, then `Write(derivation[1])`, etc., reveals one line at a time. Anchor the equation top-left on screen so new lines appear *below* earlier lines rather than pushing them around.

**Don't** animate derivation-line reveals with `TransformMatchingTex` between the partial equation and the full equation — the partial equation is a different mobject every step; the transform matching gets confused. Separate `Write` calls on the target indices read better.

### 6. The LaTeX install itself

Manim calls out to `pdflatex` (or `latex`) + `dvisvgm` behind the scenes. Packages required for Phase 1:

- `standalone` (document class Manim uses).
- `preview` (dependency).
- `doublestroke` (for `\mathbb`).
- `relsize` (for relative sizing commands).
- `everysel`, `ms`, `rsfs`, `setspace`, `tipa`, `wasy`, `wasysym`, `xcolor`, `jknapltx` (Manim transitive deps).

macOS install path:

```
brew install --cask basictex
eval "$(/usr/libexec/path_helper)"
sudo tlmgr update --self
sudo tlmgr install standalone preview doublestroke relsize everysel ms \
    rsfs setspace tipa wasy wasysym xcolor jknapltx
```

If `manim-render` fails with `LaTeX Error: File 'XXX.sty' not found`, the fix is `sudo tlmgr install <package-containing-XXX>`. The error catalog in `manim-debugging` lists the ten most common missing-package errors and the exact `tlmgr` command that fixes each.

## Examples

Six scenes under `examples/`. Every one requires a LaTeX install.

| # | File | Demonstrates |
|---|---|---|
| 01 | `example_01_sizing_hierarchy.py` | Hero/running/label font_size tiers side-by-side. |
| 02 | `example_02_color_coded_substrings.py` | Indexed `MathTex` with per-term colours. |
| 03 | `example_03_underbrace_annotation.py` | Path A and Path B annotations on the same equation. |
| 04 | `example_04_aligned_transformation.py` | `TransformMatchingTex` on `x^2 → x^3` with shared anchors. |
| 05 | `example_05_derivation_stepped.py` | Three-line `aligned` derivation revealed one step at a time. |
| 06 | `example_06_key_map_transform.py` | Explicit `key_map` on a transform where default matching picks the wrong pairing. |

Expected visual behaviour for each is documented in the file's docstring. Since these can't be CI-rendered without a LaTeX install, each file includes an `# expected frame` comment describing the final frame — useful for reviewers without a LaTeX machine.

## Gotchas / anti-patterns

- **Forgetting `r"..."` raw strings.** `"\\frac"` works, `"\frac"` produces `\x0crac`. Always raw.
- **Breaking a LaTeX token across substrings.** `r"\frac"`, `r"{d}"`, `r"{dx}"` as three strings is not the same as `r"\frac{d}{dx}"` as one. The former may render fine and then break your TransformMatchingTex six months later.
- **`Tex` when you wanted `MathTex`.** `Tex(r"x^2")` renders as literal `x^2`. Use `MathTex` for anything math.
- **Scaling LaTeX with `.scale()` beyond 1.2×.** Strokes thicken visibly. Re-create with a larger `font_size` instead.
- **Coloring by `set_color_by_tex`.** Works but is brittle against substring boundaries; prefer indexed colouring (`eq[i].set_color(...)`).
- **`TransformMatchingTex` with identical source and target.** Will warn, won't animate. Use `ReplacementTransform` instead if the transform is semantically a no-op.
- **Underbrace label too long.** If the Text below a `Brace` exceeds the brace width, the label should be shrunk with `font_size`, not the brace widened — the brace should hug what it annotates.
- **Mid-scene font_size change.** Moving from `font_size=36` on an equation to `font_size=60` as it becomes the focus produces a jarring growth. Fade the old, fade in the new at the new size, if the size change is semantically meaningful.

## Changelog

- **0.1.0** (2026-04-21) — initial Phase 1 ship. Font-size tiers, indexed substrings + colour semantics, underbrace with both LaTeX-native and Manim-Brace paths, `TransformMatchingTex` canonical uses and `key_map` override, multi-line derivations via `aligned`, install notes for macOS. Six runnable examples covering each core pattern. Paired with `manim-primitives` and `color-and-typography`.
