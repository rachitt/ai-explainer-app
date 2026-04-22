"""MoveAlongPath: a Dot orbiting a Circle.

Demonstrates: MoveAlongPath, arc-length parameterization (uniform speed).
"""
import math
from chalk import (
    Scene, Circle, Dot, MathTex,
    FadeIn, MoveAlongPath,
    YELLOW, GREY,
    SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER,
    place_in_zone,
)
from chalk.rate_funcs import linear


class MoveAlongPathDemo(Scene):
    def construct(self):
        lbl = MathTex(r"\text{MoveAlongPath}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        orbit = Circle(radius=2.0, color=GREY, stroke_width=1.2)
        dot   = Dot(point=(2.0, 0.0), radius=0.14, color=YELLOW)

        self.add(orbit, dot)
        self.play(FadeIn(orbit, run_time=0.5), FadeIn(dot, run_time=0.3))

        # Uniform-speed orbit; rate_func=linear → constant angular velocity
        self.play(MoveAlongPath(dot, orbit, run_time=5.0, rate_func=linear))
        self.wait(1.5)
