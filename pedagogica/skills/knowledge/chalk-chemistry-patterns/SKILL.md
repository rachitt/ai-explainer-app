---
name: chalk-chemistry-patterns
description: Helper-first patterns for chalk chemistry scenes. Use when generating molecule, bond, reaction-mechanism, captioned-formula, or stereochemistry animations.
---

# Chalk Chemistry Patterns

## Rule

Use `Atom`, `Bond`, `MoleculeLayout`, and `ReactionArrow` first. Hand-place atoms
for small canonical molecules; reach for `MoleculeLayout` once the molecule is
complex enough that spacing, overlap, or bond angles become the main problem.

## Component Palette

| Element | Semantic color | Typical use |
| --- | --- | --- |
| `C` | `GREY` / `PRIMARY` | carbon skeleton |
| `O` | `RED_FILL` stroke | oxygen contrast, not red text |
| `N` | `BLUE` | nitrogen |
| `H` | white-ish / `PRIMARY` | hydrogen |
| `Na` | `GREEN` | spectator or ionic partner |
| `Cl` | `GREEN` | leaving group / halide |

## CO2 Linear Template

```python
from chalk import Scene, FadeIn, PRIMARY, RED_FILL
from chalk.chemistry import Atom, Bond, MoleculeLayout


class CarbonDioxide(Scene):
    def construct(self):
        c = Atom("C", (0.0, 0.0), color=PRIMARY)
        o_l = Atom("O", (-1.6, 0.0), color=RED_FILL)
        o_r = Atom("O", (1.6, 0.0), color=RED_FILL)
        mol = MoleculeLayout([c, o_l, o_r], [Bond(o_l, c, order=2), Bond(c, o_r, order=2)])
        self.add(mol)
        self.play(FadeIn(mol))
```

## Methane Tetrahedral Template

```python
from chalk import Scene, FadeIn, PRIMARY
from chalk.chemistry import Atom, Bond, MoleculeLayout


class Methane(Scene):
    def construct(self):
        c = Atom("C", (0.0, 0.0), color=PRIMARY)
        hs = [
            Atom("H", (0.0, 1.2), color=PRIMARY),
            Atom("H", (-1.2, -0.5), color=PRIMARY),
            Atom("H", (1.2, -0.5), color=PRIMARY),
            Atom("H", (0.0, -1.3), color=PRIMARY),
        ]
        bonds = [Bond(c, hs[0]), Bond(c, hs[1], stereo="wedge"), Bond(c, hs[2], stereo="dash"), Bond(c, hs[3])]
        mol = MoleculeLayout([c, *hs], bonds)
        self.add(mol)
        self.play(FadeIn(mol))
```

## SN2 Inversion Template

```python
from chalk import Scene, FadeIn, YELLOW, GREEN, PRIMARY
from chalk.chemistry import Atom, Bond, MoleculeLayout, ReactionArrow


class SN2Inversion(Scene):
    def construct(self):
        c = Atom("C", (0.0, 0.0), color=PRIMARY)
        cl = Atom("Cl", (1.6, 0.0), color=GREEN)
        oh = Atom("OH", (-2.2, 0.0), color=PRIMARY, charge="-")
        substrate = MoleculeLayout([c, cl], [Bond(c, cl)])
        attack = ReactionArrow(oh.center, c.center, color=YELLOW)
        self.add(oh, substrate, attack)
        self.play(FadeIn(oh), FadeIn(substrate), FadeIn(attack))
```

## Formula Captions

Once `Molecule(..., caption=...)` lands, use that. For now:

```python
lbl = MathTex(r"\mathrm{CO_2}", color=PRIMARY)
next_to(lbl, molecule, direction="DOWN", buff=0.45)
```

## Common Mistakes

- Placing atom charge diagonally inside the atom circle. Use
  `Atom(symbol, charge="+")`; the helper renders charge as a superscript.
- Using `RED_FILL` as text color. It is acceptable as oxygen stroke/fill, not
  for labels or captions.
- Hand-spacing crowded molecules when `MoleculeLayout` should own the layout.
- Drawing reaction arrows as raw lines instead of `ReactionArrow`.
