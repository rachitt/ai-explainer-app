"""Write animation on a display equation.

Demonstrates: Write, MathTex, place_in_zone.
"""
from chalk import (
    Scene, MathTex, Write,
    PRIMARY, GREY,
    SCALE_DISPLAY, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER,
    place_in_zone, next_to,
)


class WriteEquation(Scene):
    def construct(self):
        title = MathTex(r"\text{The Derivative}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(title, ZONE_TOP)
        self.add(title)
        self.play(Write(title, run_time=0.8))

        eq = MathTex(
            r"f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}",
            color=PRIMARY,
            scale=SCALE_DISPLAY,
        )
        place_in_zone(eq, ZONE_CENTER)
        self.add(eq)
        self.play(Write(eq, run_time=1.8))
        self.wait(2.5)
