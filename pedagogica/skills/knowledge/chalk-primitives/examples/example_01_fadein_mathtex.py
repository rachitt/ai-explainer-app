"""FadeIn on MathTex at each scale tier.

Demonstrates: MathTex, FadeIn, place_in_zone, scale tiers.
"""
from chalk import (
    Scene, MathTex, FadeIn,
    PRIMARY, YELLOW, GREY,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
    place_in_zone, next_to,
)


class FadeInMathTex(Scene):
    def construct(self):
        display = MathTex(r"f'(x) = 2x", color=PRIMARY, scale=SCALE_DISPLAY)
        place_in_zone(display, ZONE_CENTER)

        body = MathTex(r"\text{SCALE\_BODY label}", color=YELLOW, scale=SCALE_BODY)
        place_in_zone(body, ZONE_TOP)

        annot = MathTex(r"\text{SCALE\_ANNOT caption}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(annot, ZONE_BOTTOM)

        self.add(body, display, annot)
        self.play(FadeIn(body, run_time=0.5))
        self.play(FadeIn(display, run_time=0.7))
        self.play(FadeIn(annot, run_time=0.5))
        self.wait(2.0)
