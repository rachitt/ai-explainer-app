"""TransformMatchingTex: F = ma → a = F/m.

Demonstrates: token-matched equation morphing.
Note: do NOT add eq2 to the scene; chalk adds the unmatched glyphs automatically.
"""
from chalk import (
    Scene, MathTex,
    FadeIn, Write, Circumscribe, TransformMatchingTex,
    PRIMARY, YELLOW, BLUE, GREY,
    SCALE_DISPLAY, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER,
    place_in_zone,
)


class TransformMatchingTexDemo(Scene):
    def construct(self):
        lbl = MathTex(r"\text{TransformMatchingTex}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        eq1 = MathTex(r"F = ma", color=PRIMARY, scale=SCALE_DISPLAY)
        place_in_zone(eq1, ZONE_CENTER)
        self.add(eq1)
        self.play(Write(eq1, run_time=1.0))
        self.wait(0.4)

        # Highlight before morphing
        self.play(Circumscribe(eq1, shape="rect", color=BLUE, buff=0.2, run_time=0.7))
        self.wait(0.3)

        # Target — do NOT add to scene
        eq2 = MathTex(r"a = F/m", color=YELLOW, scale=SCALE_DISPLAY)
        place_in_zone(eq2, ZONE_CENTER)

        self.play(TransformMatchingTex(eq1, eq2, run_time=1.5))
        self.wait(2.5)
