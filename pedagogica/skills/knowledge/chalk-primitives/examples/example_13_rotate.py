"""Rotate: spin a Rectangle one full turn.

Demonstrates: Rotate with about_point, ChangeValue driving a live angle label.
"""
import math
from chalk import (
    Scene, Rectangle, MathTex,
    FadeIn, Rotate, ChangeValue,
    AnimationGroup,
    ValueTracker, always_redraw,
    BLUE, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP,
    place_in_zone,
)
from chalk.rate_funcs import linear


class RotateDemo(Scene):
    def construct(self):
        lbl = MathTex(r"\text{Rotate}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        sq = Rectangle(width=2.0, height=2.0, color=BLUE, stroke_width=3.0)
        self.add(sq)
        self.play(FadeIn(sq, run_time=0.4))

        t = ValueTracker(0.0)
        angle_lbl = always_redraw(
            lambda: MathTex(
                rf"\theta = {t.get_value():.0f}^\circ",
                color=GREY, scale=SCALE_LABEL,
            ).move_to(0.0, -2.8)
        )
        self.add(angle_lbl)

        self.play(
            AnimationGroup(
                Rotate(sq, angle=2 * math.pi, about_point=(0.0, 0.0),
                       run_time=4.0, rate_func=linear),
                ChangeValue(t, 360.0, run_time=4.0, rate_func=linear),
                lag_ratio=0.0,
            )
        )
        self.wait(1.5)
