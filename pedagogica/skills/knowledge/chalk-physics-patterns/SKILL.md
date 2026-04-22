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
