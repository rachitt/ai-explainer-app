"""NumberLine + brace_label for dimension annotation.

Demonstrates: NumberLine, Dot on number line, brace_label.
"""
from chalk import (
    Scene, NumberLine, Line, Dot, MathTex,
    FadeIn, brace_label,
    YELLOW, GREY, PRIMARY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP,
    place_in_zone,
)


class NumberLineBrace(Scene):
    def construct(self):
        lbl = MathTex(r"\text{NumberLine + brace\_label}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        nl = NumberLine(x_range=(-4.0, 4.0, 1.0), length=8.0,
                        include_numbers=True, color=GREY)
        self.add(nl)
        self.play(FadeIn(nl, run_time=0.6))

        # Highlight segment [0, 3]
        seg  = Line((0.0, 0.0), (3.0, 0.0), color=YELLOW, stroke_width=4.0)
        dot0 = Dot(point=(0.0, 0.0), radius=0.10, color=YELLOW)
        dot3 = Dot(point=(3.0, 0.0), radius=0.10, color=YELLOW)
        self.add(seg, dot0, dot3)
        self.play(FadeIn(seg, run_time=0.5),
                  FadeIn(dot0, run_time=0.3), FadeIn(dot3, run_time=0.3))

        brace, blbl = brace_label(seg, r"\Delta x = 3",
                                   direction="UP", color=YELLOW, scale=SCALE_LABEL)
        self.add(brace, blbl)
        self.play(FadeIn(brace, run_time=0.5), FadeIn(blbl, run_time=0.5))
        self.wait(2.5)
