"""morph_demo: TransformMatchingTex — F=ma → a=F/m."""
from chalk import (
    Scene, MathTex, FadeIn,
    TransformMatchingTex,
    PRIMARY, YELLOW, SCALE_DISPLAY, SCALE_BODY,
    ZONE_TOP, ZONE_CENTER, place_in_zone,
)


class MorphDemo(Scene):
    def construct(self) -> None:
        title = MathTex(r"\text{Newton's Second Law}", color=PRIMARY, scale=SCALE_BODY)
        place_in_zone(title, ZONE_TOP)
        self.add(title)
        self.play(FadeIn(title, run_time=0.6))

        eq1 = MathTex(r"F=ma", color=PRIMARY, scale=SCALE_DISPLAY)
        place_in_zone(eq1, ZONE_CENTER)
        self.add(eq1)
        self.play(FadeIn(eq1, run_time=0.8))
        self.wait(1.0)

        eq2 = MathTex(r"a=F/m", color=YELLOW, scale=SCALE_DISPLAY)
        place_in_zone(eq2, ZONE_CENTER)

        self.play(TransformMatchingTex(eq1, eq2, run_time=1.5))
        self.wait(2.0)
