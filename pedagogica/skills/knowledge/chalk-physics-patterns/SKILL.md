---
name: chalk-physics-patterns
description: Helper-first patterns for chalk physics scenes. Use when generating projectile, pendulum, spring-mass, force-vector, or free-body animations.
---

# Chalk Physics Patterns

## Rule

Reach for `FreeBody(...)`, `Mass`, `Spring`, `Pendulum`, and `Vector` before
hand-placing arrows or labels. Compose domain helpers; do not rebuild them from
raw `Circle`, `Line`, and `Arrow` unless the helper cannot express the scene.

## Component Palette

| Component | Semantic color | Typical use |
| --- | --- | --- |
| `Mass` | `BLUE` | moving object, variable state |
| `Spring` | `PRIMARY` | restoring mechanism |
| `Vector` | `YELLOW` | force or highlighted direction |
| `Pendulum` | `BLUE` + `PRIMARY` | bob plus rod/string |

## Projectile Template

```python
from chalk import Scene, FadeIn, MoveAlongPath, ParametricFunction, YELLOW
from chalk.physics import Mass, Vector


class Projectile(Scene):
    def construct(self):
        ball = Mass((-4.0, -1.8), label="m")
        path = ParametricFunction(lambda t: (-4.0 + 8.0 * t, -1.8 + 4.0 * t - 4.0 * t * t), color=YELLOW)
        velocity = Vector(ball, (-3.0, -0.9), label="v_0", color=YELLOW)
        self.add(path, ball, velocity)
        self.play(FadeIn(path), FadeIn(ball), FadeIn(velocity))
        self.play(MoveAlongPath(ball, path, run_time=2.5))
```

## Pendulum Template

```python
from chalk import Scene, FadeIn, ChangeValue, ValueTracker
from chalk.physics import Pendulum


class PendulumSwing(Scene):
    def construct(self):
        angle = ValueTracker(0.45)
        pend = Pendulum(pivot=(0.0, 2.5), length=2.7, angle_tracker=angle)
        self.add(pend)
        self.play(FadeIn(pend))
        self.play(ChangeValue(angle, -0.45, run_time=1.4))
        self.play(ChangeValue(angle, 0.45, run_time=1.4))
```

## Spring-Mass Template

```python
from chalk import Scene, FadeIn, ChangeValue, ValueTracker, always_redraw, PRIMARY
from chalk.physics import Mass, Spring


class SpringMass(Scene):
    def construct(self):
        x = ValueTracker(-2.2)
        mass = always_redraw(lambda: Mass((x.get_value(), 0.0), label="m", show_weight=False))
        spring = always_redraw(lambda: Spring((-5.0, 0.0), mass, color=PRIMARY))
        self.add(spring, mass)
        self.play(FadeIn(spring), FadeIn(mass))
        self.play(ChangeValue(x, -1.2, run_time=1.2))
```

## Free-Body Template

```python
from chalk.physics import FreeBody

fbd = FreeBody(label="m", forces=[(1.4, 90.0, "N"), (1.4, 270.0, "W")])
```

Use `FreeBody(...)` over hand-placed force arrows. It handles radial placement,
labels, and consistent arrow lengths.

## Common Mistakes

- Calling `Vector(tuple, tuple)` with guessed coordinates when the vector should
  originate from a `Mass` object.
- Placing the weight arrow manually below a mass instead of `show_weight=True`.
- Leaving labels behind when a mass moves; animate the mass and labels together
  or use redraw helpers.
- Using `RED_FILL` for force text; reserve red for object contrast, not labels.

## Pedagogy arc pairing — projectile scene (canonical)

Physics scenes fit the storyboard pedagogy arc naturally: throw the object first (hook), predict where it lands (struggle), then decompose into x/y components (resolve). Use composites to keep beat timing predictable.

```python
from chalk import (
    Scene, FadeIn, ParametricFunction, MathTex, YELLOW, BLUE, GREY, SCALE_BODY,
    reveal_then_explain, highlight_and_hold, build_up_sequence,
    ZONE_TOP, place_in_zone,
)
from chalk.physics import Mass, Vector


class ProjectileStruggleReveal(Scene):
    def construct(self):
        # Hook: ball sits at launch, path is hidden.
        ball = Mass((-4.0, -1.8), label="m")
        v0 = Vector(ball, (-3.0, -0.9), label="v_0", color=YELLOW)
        question = MathTex(r"\text{where does it land?}", color=GREY, scale=SCALE_BODY)
        place_in_zone(question, ZONE_TOP)

        self.play(reveal_then_explain(ball, question, run_time=1.8))
        self.play(FadeIn(v0), run_time=0.5)

        # Struggle: pause on the throw before revealing the arc.
        self.play(highlight_and_hold(ball, color=YELLOW, hold_seconds=1.6))

        # Resolve: trace the arc progressively with apex + landing annotations.
        path = ParametricFunction(
            lambda t: (-4.0 + 8.0 * t, -1.8 + 4.0 * t - 4.0 * t * t), color=YELLOW
        )
        apex_label = MathTex(r"h_{\max}", color=BLUE, scale=SCALE_BODY)
        land_label = MathTex(r"R", color=BLUE, scale=SCALE_BODY)

        self.play(
            build_up_sequence(
                [
                    (path,),                      # curve draw (defaults to Write)
                    (apex_label, FadeIn),
                    (land_label, FadeIn),
                ],
                step_run_time=1.2,
                inter_step_pause=0.3,
            )
        )
```

**Why it teaches.** Hook (throw pose + question), Struggle (hold on the unthrown ball), Resolve (progressive arc + annotations). The viewer predicts the landing before the arc draws — then checks their guess against the reveal.

## Composite pairings for physics scenes

| composite | physics use |
|---|---|
| `reveal_then_explain(object, caption)` | Introduce mass / pendulum / spring + the quantity being tracked. |
| `highlight_and_hold(mass, hold_seconds=1.5)` | Before motion starts (prediction beat) and after it ends (result beat). |
| `build_up_sequence` | FBD force arrows one-by-one, so the viewer tracks each contribution. |
| `animated_wait_with_pulse(targets=[mass])` | Narration overruns the motion — pulse the mass instead of freezing. |
