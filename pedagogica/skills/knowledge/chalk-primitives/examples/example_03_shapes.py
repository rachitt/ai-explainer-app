"""Circle, Rectangle, Line, Arrow — the basic shapes.

Demonstrates: shape constructors, shift, FadeIn, LaggedStart.
"""
from chalk import (
    Scene, Circle, Rectangle, Line, Arrow,
    MathTex, FadeIn, LaggedStart,
    BLUE, GREEN, GREY, PRIMARY,
    SCALE_LABEL,
    ZONE_TOP, ZONE_CENTER,
    place_in_zone, next_to,
)


class BasicShapes(Scene):
    def construct(self):
        lbl = MathTex(r"\text{Shapes}", color=GREY, scale=SCALE_LABEL)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        circ = Circle(radius=0.8, color=BLUE, stroke_width=2.5)
        circ.shift(-3.5, 0.0)

        rect = Rectangle(width=2.0, height=1.2, color=GREEN, stroke_width=2.5)

        line = Line((-1.0, -1.5), (1.0, -1.5), color=GREY, stroke_width=1.5)

        arr = Arrow((2.5, -0.4), (4.5, -0.4), color=PRIMARY, stroke_width=2.0)

        self.add(circ, rect, line, arr)
        self.play(
            LaggedStart(
                FadeIn(circ, run_time=0.6),
                FadeIn(rect, run_time=0.6),
                FadeIn(line, run_time=0.5),
                FadeIn(arr,  run_time=0.5),
                lag_ratio=0.3,
            )
        )
        self.wait(2.0)
