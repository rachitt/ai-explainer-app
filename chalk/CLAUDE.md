# chalk authoring rules

Read this every session before writing a scene. These rules govern how scenes
look and feel. Violations show up as amateur-looking output.

## Import rule

Never write raw hex colors, magic-number scales, or hardcoded zone y-coordinates
inside a scene file. Import them:

```python
from chalk import (
    Scene, Circle, Line, MathTex,
    ShiftAnim, FadeIn, FadeOut,
    PRIMARY, YELLOW, BLUE, GREEN, RED_FILL, GREY, TRACK,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
    next_to, place_in_zone,
)
```

If a scene needs a color or a size that isn't in `style.py`, update `style.py`
first — don't inline new values. One palette, one type scale, enforced.

## Palette semantics

| Constant   | Use for                                                          |
|------------|------------------------------------------------------------------|
| `PRIMARY`  | main text, primary math, the thing the viewer is looking at      |
| `YELLOW`   | result, punchline, key quantity being computed toward            |
| `BLUE`     | variable, moving thing, free input                               |
| `GREEN`    | correct / target / "yes, this" confirmation                      |
| `RED_FILL` | contrast / "not this" — **FILL OR STROKE ONLY**, never on text   |
| `GREY`     | annotations, axis labels, secondary captions                     |
| `TRACK`    | subtle reference lines (ground tracks, gridlines)                |

Hard rules:
- `RED_FILL` fails WCAG AA-large as text. Never pass it as `MathTex(color=RED_FILL)`.
  For a red object's label, use `PRIMARY` — proximity communicates the pairing.
- Green = correct, red = wrong. Never invert. These map to cultural expectations.
- One semantic role per element per scene. If narrative needs to reclassify an
  element, fade it out and reintroduce a new one.
- At most **4 semantic slots active** in any scene. Above that, the color key
  becomes the cognitive load.

## Type scale

Use the named tiers; don't invent sizes.

| Tier             | Use for                                                      |
|------------------|--------------------------------------------------------------|
| `SCALE_DISPLAY`  | the main equation of a beat (at most one per rest frame)     |
| `SCALE_BODY`     | secondary equations, substitutions                           |
| `SCALE_LABEL`    | labels on objects (mass, axis, point labels)                 |
| `SCALE_ANNOT`    | small annotations, captions, derived restatements            |

`SCALE_MIN = 0.40` is the floor. If a layout seems to need smaller text, the
layout is wrong — drop an element, not the scale.

## Zones and safe area

Frame is 14.2 × 8.0. Safe area: `SAFE_X ⊂ [-6.6, 6.6]`, `SAFE_Y ⊂ [-3.5, 3.5]`.

Three bands:
- `ZONE_TOP = (2.0, 3.5)` — beat title, law statement
- `ZONE_CENTER = (-2.0, 2.0)` — main visual (balls, graphs, diagrams)
- `ZONE_BOTTOM = (-3.5, -2.0)` — running step, result caption, payoff

Use **at most 3 zones active** at any rest frame. Empty zones aren't waste —
they are breathing room. Reading order is top → center → bottom.

## Placement

Prefer `next_to(mob, anchor, direction="UP"|"DOWN"|"LEFT"|"RIGHT", buff=0.3)`
over raw `move_to(x, y)` math. This keeps relative spacing consistent across
scenes and prevents the "label stuck while ball moves" failure mode.

```python
ball = Circle(radius=0.3, ...)
ball.shift(-5.0, 1.0)
label = MathTex(r"m = 1\,\mathrm{kg}", color=BLUE, scale=SCALE_LABEL)
next_to(label, ball, direction="UP", buff=0.3)
```

## Scene-transition pattern (clear between beats)

**This is the most important rule.** A video is a sequence of beats, not one
infinite canvas. When a beat ends and the next begins, the screen must reset.
Otherwise every element from every beat piles up on screen.

Use `self.clear()` at the end of every beat (except the last):

```python
# ── Beat 1: title ────────────────────────────
self.add(title)
self.play(FadeIn(title, run_time=0.8))
self.wait(2.0)
self.clear()

# ── Beat 2: the demo ─────────────────────────
self.add(circle, label)
self.play(FadeIn(circle, run_time=0.6), FadeIn(label, run_time=0.6))
# ... beat plays ...
self.clear()

# ── Beat 3: the result ───────────────────────
...
```

`self.clear(run_time=0.5, keep=[persistent_mob])` fades out every added mobject
except those in `keep`.  Use `keep` when one element anchors multiple beats
(e.g. an agent circle that stays while tools fan out around it).

**Anti-pattern:** keep calling `self.add()` and `self.play(FadeIn(...))` across
five beats without ever calling `self.clear()`.  By the end, the title is
still visible underneath the payoff caption.  Don't do this.

## Arrows between objects (never hand-pick start/end coordinates)

If you need an arrow from one mobject to another, **use `arrow_between()`**.
It reads the source and target bboxes, shoots a ray between their centers,
and anchors the arrow at their edges with a `buff` gap.

```python
arrow = arrow_between(prompt_box, agent_circle, buff=0.15, color=PRIMARY)
self.add(arrow)
self.play(FadeIn(arrow, run_time=0.4))
```

The source or target can be a VMobject (Circle, Rectangle, Arrow) or a VGroup
(MathTex label, a grouped assembly).  The arrow will anchor at the bbox edge
of whichever shape you pass.

**Anti-pattern:** computing start=(source.x + source.width/2 + 0.1, ...) by
hand, or hardcoding coordinates like `Arrow((-1.7, 0.0), (2.0, 0.0))`. This
breaks every time a label resizes or a shape moves. One source of truth: the
bboxes.

## Boxed labels (never hand-size a Rectangle around text)

If you need a labeled box (resistor, tool, file, component), **use
`labeled_box()`**.  Hand-sizing a Rectangle with hardcoded width/height and
dropping a MathTex on top is the reason labels end up spilling out the sides.

```python
box, lbl = labeled_box(r"\mathrm{README}", color=GREY, scale=SCALE_LABEL)
# Both are centered at origin; shift them as a pair.
box.shift(3.5, 0.4)
lbl.move_to(3.5, 0.4)
self.add(box, lbl)
```

`labeled_box` measures the label's bbox and sizes the rectangle with padding
so the text always fits. Optional args: `pad_x`, `pad_y`, `min_width`,
`min_height`, `fill_color`, `fill_opacity`, `label_color`.

**Anti-pattern:** `Rectangle(width=2.0, height=0.9)` + a separate
`MathTex(r"\mathrm{README}")` placed at the same center.  One word change to
the label and the text now extends past the box on either side.

## Reveal pattern (never pop in)

Elements must fade in, not appear abruptly. After `self.add(...)`, immediately
`self.play(FadeIn(...))`:

```python
self.add(law)
self.play(FadeIn(law, run_time=0.7))
self.wait(0.9)
```

Raw `self.add(mob)` without a following FadeIn is an anti-pattern — the viewer
gets no visual cue that a new element arrived.

## Motion pattern (labels ride with objects)

If an object has a label (mass label, point label), the label moves WITH the
object. Use parallel `ShiftAnim`:

```python
self.play(
    ShiftAnim(ball,     dx=9.0, dy=0.0, run_time=3.0),
    ShiftAnim(ball_lbl, dx=9.0, dy=0.0, run_time=3.0),
    run_time=3.0,
)
```

A label left behind while its object moved is a classic readability failure.

## Pacing

- FadeIn for a title: 0.6–0.8 s
- FadeIn for a supporting element: 0.4–0.6 s
- Hold after a reveal: ≥ 0.8 s before the next change
- Motion run_time: 2.0–3.5 s for a comparison; 1.0–1.5 s for a simple slide
- Final hold: ≥ 2.0 s so the payoff reads

Don't cram acts together. Give the viewer time to read.

## Canonical example

See `chalk/examples/newton.py` — Newton's Second Law demonstrates every rule
above: imported palette, named scales, zones, `next_to` (when we add one to
newton later), fade-in reveals, `ShiftAnim` with parallel label motion.

## Anti-patterns

- Raw hex in scene code — use constants from `chalk.style`
- `scale=0.37` or any non-tier scale — pick the right tier or update `style.py`
- Label positioned with `move_to(x, y)` where y is a magic number — use `next_to`
- `self.add(mob)` with no following `FadeIn` reveal
- Label shifted separately from its parent object — use parallel `ShiftAnim`
- `MathTex(color=RED_FILL)` — red fails text contrast; use `PRIMARY`
- Four or more active semantic color slots per scene — trim

## When a rule doesn't fit

If a scene genuinely needs something the rules don't allow, update `style.py`,
`layout.py`, or this CLAUDE.md **first**, in the same commit. The rules are the
single source of truth; scenes are consumers.

## Positional kits — prevent overlap

chalk has NO auto-layout. Graph, MoleculeLayout, and other positional kits require the scene author (LLM) to hand-place every coordinate. Use grid templates from the chalk-graph-patterns skill for graphs, RDKit 2D coords for molecules via MoleculeLayout.from_smiles, and chalk.layout.check_no_overlap to validate at construction time. Auto-placement algorithms from_adjacency, _spring_layout, etc have been removed — do not try to call them.
