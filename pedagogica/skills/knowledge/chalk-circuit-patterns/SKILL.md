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

## KirchhoffDemo — always pass the numbers for physics scenes

`chalk.circuits.KirchhoffDemo(...)` is the canonical series R1-R2 loop. For any scene that teaches Ohm's law or KVL, pass the numeric physics so the helper auto-fills the current label AND renders per-component voltage drops. A scene that shows `R_1` / `R_2` / `V` symbols but not the voltages across them fails the viewer — they have no way to cash "three volts dropped" against anything on screen.

```python
from chalk import Scene, FadeIn, GREEN, BLUE, YELLOW
from chalk.circuits import KirchhoffDemo


class KVLPhysics(Scene):
    def construct(self):
        circuit = KirchhoffDemo(
            battery_emf=r"9\,\mathrm{V}",
            r1_label=r"3\,\Omega",
            r2_label=r"6\,\Omega",
            battery_volts=9.0,
            r1_ohms=3.0,
            r2_ohms=6.0,
            show_voltage_drops=True,
            color_battery=GREEN,
            color_resistor=BLUE,
            color_current=YELLOW,
        )
        self.add(circuit)
        self.play(FadeIn(circuit, run_time=1.2))
```

What the helper renders when you pass all three numbers:

- Current label on the loop: `I = 1 A` (auto-computed from `V / (R1 + R2)`).
- If `show_voltage_drops=True`: per-component signed voltage labels — `+9 V` across the battery, `-3 V` across R1, `-6 V` across R2 — the three numbers sum to zero by construction, which is the whole point of KVL made visible.

**Do not hand-place voltage labels on the components.** The helper anchors them inside the loop so they never clash with the existing `r1_label` / `r2_label` / battery label. Hand-placed labels are a recurring source of preflight overlap failures — use the `show_voltage_drops=True` flag instead.

Anti-pattern (what not to do):

```python
# ❌ Hand-placed labels routinely clash with KirchhoffDemo's built-in
# resistor labels at the same anchor points.
v_r1 = MathTex(r"-3\,\mathrm{V}", color=BLUE, scale=SCALE_LABEL)
v_r1.move_to(0.0, 2.15)  # collides with r1_label from KirchhoffDemo
```

Correct:

```python
# ✓ Let the helper place signed voltage labels inside the loop, clear
# of every other anchor. One source of truth for geometry.
circuit = KirchhoffDemo(..., show_voltage_drops=True)
```

## KVL loop-walker pattern (canonical)

KVL scenes almost always benefit from the same visual trick: a traveler dot walks the loop once, and a running voltage tally in `ZONE_TOP` stamps each signed contribution as the walker crosses a component. This makes the abstract "directed sum around a loop" concrete.

```python
from chalk import (
    Scene, MathTex, DecimalNumber, ValueTracker, ChangeValue,
    Dot, FadeIn, always_redraw,
    reveal_then_explain, highlight_and_hold, build_up_sequence,
    YELLOW, PRIMARY, GREEN, BLUE, GREY,
    SCALE_DISPLAY, SCALE_BODY,
    ZONE_TOP, place_in_zone,
)
from chalk.circuits import Battery, Resistor, Wire


class KVLLoopWalker(Scene):
    def construct(self):
        batt = Battery((-4.0, -0.3), (-4.0, 0.3), color=GREEN)
        r1 = Resistor((-1.5, 1.5), (1.5, 1.5), color=PRIMARY)
        r2 = Resistor((4.0, -0.3), (4.0, 0.3), color=PRIMARY)
        loop = Wire(
            (-4, 0.3), (-4, 1.5), (4, 1.5), (4, 0.3),
            (4, -0.3), (4, -1.5), (-4, -1.5), (-4, -0.3),
            breaks=[batt, r1, r2],
        )

        # Beat 1: reveal circuit + pose the question in one staggered move.
        question = MathTex(r"\sum_{\text{loop}} V = 0 \;\; ?", color=GREY, scale=SCALE_BODY)
        place_in_zone(question, ZONE_TOP)
        self.play(reveal_then_explain(loop, question, run_time=2.0))
        self.play(FadeIn(batt), FadeIn(r1), FadeIn(r2), run_time=0.8)

        # Beat 2: running tally + walker travel around the loop.
        tally = ValueTracker(0.0)
        tally_readout = always_redraw(
            lambda: DecimalNumber(tally.get_value(), num_decimal_places=1, color=YELLOW, scale=SCALE_DISPLAY)
                .move_to((0.0, 2.8))
        )
        walker = Dot(point=(-4.0, 0.0), color=YELLOW)
        self.add(tally_readout, walker)

        # Each leg of the walk stamps its signed voltage as it completes.
        # +9 rising across battery, -3 across r1, -6 across r2 = 0.
        self.play(
            build_up_sequence(
                [
                    (walker, lambda m: ChangeValue(m.position, (-4.0, 1.5), run_time=1.0)),
                    (tally, lambda m: ChangeValue(m, 9.0, run_time=0.8)),
                    (walker, lambda m: ChangeValue(m.position, (4.0, 1.5), run_time=1.2)),
                    (tally, lambda m: ChangeValue(m, 6.0, run_time=0.6)),
                    (walker, lambda m: ChangeValue(m.position, (4.0, -1.5), run_time=1.0)),
                    (tally, lambda m: ChangeValue(m, 0.0, run_time=0.8)),
                    (walker, lambda m: ChangeValue(m.position, (-4.0, -1.5), run_time=1.0)),
                    (walker, lambda m: ChangeValue(m.position, (-4.0, 0.0), run_time=0.6)),
                ],
                step_run_time=1.0,
                inter_step_pause=0.2,
            )
        )

        # Beat 3: hold on the zero tally so the viewer registers the landing.
        self.play(highlight_and_hold(tally_readout, color=GREEN, hold_seconds=1.5))
```

**Why it teaches.** The tally is the hook answer made concrete — before naming KVL, the viewer watches the number return to zero and wonders why. Reveal the rule after the demo. This matches the storyboard SKILL's pedagogy arc (Hook → Concrete → Struggle → Resolve).

**Run-time budget.** ~15s. If the scene's `target_duration_seconds` is larger (e.g. a 42s `define` beat), extend with a second lap showing a different component sign convention, or add `animated_wait_with_pulse(targets=[tally_readout], pad_seconds=...)` rather than freezing.

## Composite pairings for circuit scenes

| composite | circuit use |
|---|---|
| `reveal_then_explain(loop_wire, law_label)` | Scene-opening. Wire draws, law statement slides in. |
| `build_up_sequence([...])` | Sequential component placement or walker travel (see KVL pattern above). |
| `highlight_and_hold(readout, hold_seconds=1.5)` | After any computed value lands — current, tally, voltage drop. |
| `animated_wait_with_pulse(targets=[component], pad_seconds=...)` | When narration over-runs the circuit animation. Never freeze the frame on a static circuit for >5s. |
