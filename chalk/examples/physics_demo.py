"""chalk.physics demo — Spring, Pendulum, Mass, Vector, FreeBody.

Run: uv run python -m chalk.cli chalk/examples/physics_demo.py PhysicsDemo
"""
import math
from chalk import (
    Scene, VGroup, ValueTracker,
    FadeIn, FadeOut, ChangeValue, Succession,
    Rectangle,
    PRIMARY, YELLOW, BLUE, GREEN, GREY,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
    place_in_zone, next_to,
)
from chalk.physics import Spring, Pendulum, Mass, Vector, FreeBody


class PhysicsDemo(Scene):
    def construct(self):

        # ── Beat 1: spring-mass system ───────────────────────────────────────
        wall = Rectangle(
            width=0.6,
            height=1.5,
            color=GREY,
            fill_color=GREY,
            fill_opacity=0.4,
            stroke_width=2.0,
        )
        wall.shift(-5.5, 0.0)
        mass = Mass((-2.2, 0.0), label="m", show_weight=False)
        spring = Spring((-5.2, 0.0), mass, coils=6, color=PRIMARY)
        label_k = Vector((-4.0, 0.8), (-3.0, 0.8), label="k", color=GREY)
        self.add(wall, spring, mass, label_k)
        self.play(
            FadeIn(wall, run_time=0.4),
            FadeIn(spring, run_time=0.6),
            FadeIn(mass, run_time=0.5),
            FadeIn(label_k, run_time=0.4),
        )
        self.wait(1.5)
        self.clear()

        # ── Beat 2: pendulum swinging ────────────────────────────────────────
        tracker = ValueTracker(0.5)
        pend = Pendulum(pivot=(0.0, 2.5), length=2.5, angle_tracker=tracker)
        self.add(pend)
        self.play(FadeIn(pend, run_time=0.4))
        self.play(ChangeValue(tracker, -0.5, run_time=1.5))
        self.play(ChangeValue(tracker, 0.5, run_time=1.5))
        self.wait(0.5)
        self.clear()

        # ── Beat 3: free body diagram ────────────────────────────────────────
        fb = FreeBody(
            label="m",
            forces=[
                (1.5, 90.0,  r"N"),
                (1.5, 270.0, r"W"),
                (1.0, 0.0,   r"F"),
            ],
        )
        self.add(fb)
        self.play(FadeIn(fb, run_time=0.6))
        self.wait(2.0)
        self.clear()
