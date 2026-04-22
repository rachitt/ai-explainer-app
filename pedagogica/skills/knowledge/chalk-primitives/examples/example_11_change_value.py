"""ChangeValue: explicit sweep with different rate functions.

Demonstrates: ChangeValue, linear vs smooth rate, two trackers in parallel.
"""
from chalk import (
    Scene, MathTex, DecimalNumber, ValueTracker,
    FadeIn, ChangeValue, AnimationGroup,
    PRIMARY, YELLOW, GREY,
    SCALE_DISPLAY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
    place_in_zone, next_to,
)
from chalk.rate_funcs import linear, smooth


class ChangeValueDemo(Scene):
    def construct(self):
        lbl = MathTex(r"\text{ChangeValue: linear vs smooth}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        t_lin  = ValueTracker(0.0)
        t_smo  = ValueTracker(0.0)

        lbl_lin = MathTex(r"\text{linear}", color=PRIMARY, scale=SCALE_LABEL)
        lbl_smo = MathTex(r"\text{smooth}", color=YELLOW, scale=SCALE_LABEL)

        cnt_lin = DecimalNumber(t_lin, num_decimal_places=1, color=PRIMARY, scale=SCALE_DISPLAY)
        cnt_smo = DecimalNumber(t_smo, num_decimal_places=1, color=YELLOW, scale=SCALE_DISPLAY)

        cnt_lin.move_to(-2.5, 0.0)
        cnt_smo.move_to( 2.5, 0.0)
        next_to(lbl_lin, cnt_lin, direction="UP", buff=0.4)
        next_to(lbl_smo, cnt_smo, direction="UP", buff=0.4)

        self.add(lbl_lin, lbl_smo, cnt_lin, cnt_smo)
        self.play(
            FadeIn(lbl_lin, run_time=0.4),
            FadeIn(lbl_smo, run_time=0.4),
        )

        # Run both simultaneously with different rate functions
        self.play(
            AnimationGroup(
                ChangeValue(t_lin, 10.0, run_time=4.0, rate_func=linear),
                ChangeValue(t_smo, 10.0, run_time=4.0, rate_func=smooth),
                lag_ratio=0.0,
            )
        )
        self.wait(2.0)
