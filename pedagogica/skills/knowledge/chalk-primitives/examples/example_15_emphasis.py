"""Indicate, Flash, Circumscribe — emphasis animations.

Note: Flash requires pre-adding its mobjects before playing.
"""
from chalk import (
    Scene, Circle, MathTex,
    FadeIn, Indicate, Flash, Circumscribe,
    BLUE, YELLOW, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER,
    place_in_zone, next_to,
)


class EmphasisDemo(Scene):
    def construct(self):
        lbl = MathTex(r"\text{Indicate, Flash, Circumscribe}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        circ = Circle(radius=0.9, color=BLUE, stroke_width=3.0)
        place_in_zone(circ, ZONE_CENTER)
        self.add(circ)
        self.play(FadeIn(circ, run_time=0.5))
        self.wait(0.3)

        # Indicate: scale-and-recolor pulse
        self.play(Indicate(circ, scale_factor=1.3, color=YELLOW, run_time=0.7))
        self.wait(0.4)

        # Circumscribe: animated rect outline
        self.play(Circumscribe(circ, shape="circle", color=YELLOW, buff=0.15, run_time=0.8))
        self.wait(0.4)

        # Flash: radial burst — must pre-add mobjects
        flash = Flash((0.0, 0.0), color=YELLOW, num_lines=12, line_length=0.35, run_time=0.5)
        for m in flash.mobjects:
            self.add(m)
        self.play(flash)
        self.wait(1.5)
