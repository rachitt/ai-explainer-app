---
name: chalk-circuit-patterns
description: Circuit placement patterns for chalk Wire/Resistor/Battery/Capacitor/Inductor/Switch scenes. Use when generating any circuit, Kirchhoff loop, RC/RL/RLC, or current-flow animation.
---

# Chalk Circuit Patterns

## Rule

Create series components first. Then draw the enclosing `Wire` with
`breaks=[...]` referencing every component whose endpoints lie on the wire.
Never draw the wire first and overlay components.

## Component Palette

| Component | Semantic color | Typical use |
| --- | --- | --- |
| `Resistor` | `PRIMARY` | resistance, load, voltage drop |
| `Battery` | `GREEN` | source, supplied voltage |
| `Capacitor` | `BLUE` | stored charge, RC transient |
| `Inductor` | `PRIMARY` | stored magnetic energy, RL transient |
| `Switch` | `PRIMARY` | open/closed control point |
| `Wire` | `GREY` | passive circuit path |
| `CurrentFlow` | `YELLOW` | moving conventional current dots |

## Canonical Loop Pattern

```python
from chalk import Scene, FadeIn, PRIMARY, GREEN, BLUE
from chalk.circuits import Battery, Capacitor, Resistor, Wire


class RCSeriesLoop(Scene):
    def construct(self):
        r = Resistor((-1.5, 1.5), (1.5, 1.5), color=PRIMARY)
        c = Capacitor((2.0, 1.5), (3.5, 1.5), color=BLUE)
        batt = Battery((-4.0, -0.3), (-4.0, 0.3), color=GREEN)
        loop = Wire(
            (-4, 1.5), (4, 1.5), (4, -1.5), (-4, -1.5), (-4, 1.5),
            breaks=[r, c, batt],
        )

        self.add(loop, r, c, batt)
        self.play(FadeIn(loop), FadeIn(r), FadeIn(c), FadeIn(batt))
        self.wait(1.0)
```

Components are created first. The wire is declared with a `breaks` list
referring to them. `Wire` auto-splits at each component's `(start, end)`,
leaving a gap exactly the size of the component.

## Current Flow

```python
from chalk import ChangeValue, YELLOW
from chalk.circuits import CurrentFlow

flow = CurrentFlow(loop, charge_count=12, color=YELLOW)
self.add(flow)
self.play(ChangeValue(flow.phase, 1.0), run_time=2.0)
```

Dots follow the wire segments and visually skip component gaps automatically.

## VoltageLabel Tips

Use the built-in `VoltageLabel` on short edges such as batteries. It places the
`V` label and +/- markers to avoid overlap with battery plates.

## Kirchhoff Loop Template

Use `chalk.circuits.KirchhoffDemo` as the canonical assembled loop before
inventing a new arrangement.

## Common Mistakes

- Forgetting `breaks=[]` -> grey stroke through the component.
- Ground in `breaks` -> raises `ValueError`; Ground is a point symbol.
- Component endpoints not collinear with the wire segment -> raises
  `ValueError`; adjust the component or wire path.
- Hand-splitting the wire into 4 stubs instead of using `breaks`.
