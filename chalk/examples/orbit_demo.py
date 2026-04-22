"""orbit_demo: a Dot orbiting a Circle path for 4 seconds."""
from chalk import (
    Scene, Circle, MathTex, FadeIn, MoveAlongPath,
    PRIMARY, BLUE, YELLOW, SCALE_BODY,
    ZONE_TOP, place_in_zone,
)
from chalk.rate_funcs import linear


class OrbitDemo(Scene):
    def construct(self):
        title = MathTex(r"\text{MoveAlongPath demo}", color=PRIMARY, scale=SCALE_BODY)
        place_in_zone(title, ZONE_TOP)
        self.add(title)
        self.play(FadeIn(title, run_time=0.6))

        orbit = Circle(radius=2.0, color=BLUE, stroke_width=1.5)
        self.add(orbit)
        self.play(FadeIn(orbit, run_time=0.5))

        dot = Circle(radius=0.12, color=YELLOW, fill_color=YELLOW, fill_opacity=1.0, stroke_width=0.0)
        self.add(dot)
        self.play(FadeIn(dot, run_time=0.3))

        self.play(MoveAlongPath(dot, orbit, run_time=4.0, rate_func=linear))
        self.wait(1.0)
