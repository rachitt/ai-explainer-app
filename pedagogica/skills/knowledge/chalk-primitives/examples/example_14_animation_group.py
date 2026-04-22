"""AnimationGroup, LaggedStart, Succession.

Demonstrates: lag_ratio behavior, Succession back-to-back.
"""
from chalk import (
    Scene, Circle, Rectangle, MathTex,
    FadeIn, FadeOut,
    AnimationGroup, LaggedStart, Succession,
    BLUE, GREEN, YELLOW, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP,
    place_in_zone,
)


class AnimationGroupDemo(Scene):
    def construct(self):
        lbl = MathTex(r"\text{AnimationGroup + LaggedStart + Succession}",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        c1 = Circle(radius=0.6, color=BLUE,  stroke_width=2.5); c1.shift(-3.5, 0.0)
        c2 = Circle(radius=0.6, color=GREEN, stroke_width=2.5); c2.shift(-1.0, 0.0)
        c3 = Circle(radius=0.6, color=YELLOW,stroke_width=2.5); c3.shift( 1.5, 0.0)
        r1 = Rectangle(width=1.0, height=1.0, color=BLUE,  stroke_width=2.5); r1.shift(-3.5, 0.0)
        r2 = Rectangle(width=1.0, height=1.0, color=GREEN, stroke_width=2.5); r2.shift(-1.0, 0.0)
        r3 = Rectangle(width=1.0, height=1.0, color=YELLOW,stroke_width=2.5); r3.shift( 1.5, 0.0)

        # LaggedStart: circles fade in with stagger
        self.add(c1, c2, c3)
        self.play(LaggedStart(
            FadeIn(c1, run_time=0.6),
            FadeIn(c2, run_time=0.6),
            FadeIn(c3, run_time=0.6),
            lag_ratio=0.4,
        ))
        self.wait(0.5)

        # Succession: replace one by one
        self.add(r1, r2, r3)
        self.play(Succession(
            FadeOut(c1, run_time=0.4),
            FadeOut(c2, run_time=0.4),
            FadeOut(c3, run_time=0.4),
        ))
        self.play(LaggedStart(
            FadeIn(r1, run_time=0.5),
            FadeIn(r2, run_time=0.5),
            FadeIn(r3, run_time=0.5),
            lag_ratio=0.3,
        ))
        self.wait(2.0)
