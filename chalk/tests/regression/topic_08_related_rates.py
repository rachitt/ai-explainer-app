"""Pattern 10 — Related rates: balloon inflating.

dV/dt = constant. r grows; dr/dt = dV/dt / (4πr²) decreases.
Three DecimalNumber readouts show the relationship in real time.
"""
import math
from chalk import (
    Scene, Circle, MathTex,
    FadeIn, Write, ChangeValue,
    ValueTracker, DecimalNumber, always_redraw,
    AnimationGroup,
    PRIMARY, YELLOW, BLUE, GREY,
    SCALE_DISPLAY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone, next_to,
)
from chalk.rate_funcs import linear


dV_dt = 2.0  # world units³/s (constant)


class RelatedRatesBalloon(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Related rates: balloon with } \frac{dV}{dt} = 2",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        # ── Setup ────────────────────────────────────────────────
        self.section("setup")
        r = ValueTracker(0.4)

        balloon = always_redraw(
            lambda: Circle(radius=r.get_value(), color=BLUE, stroke_width=2.5)
        )
        balloon_fill = always_redraw(
            lambda: Circle(
                radius=r.get_value(),
                fill_color=BLUE, fill_opacity=0.20,
                color=BLUE, stroke_width=0.0,
            )
        )

        self.add(balloon_fill, balloon)
        self.play(FadeIn(balloon, run_time=0.4))

        # Readouts
        r_tracker    = r
        V_tracker    = ValueTracker((4 / 3) * math.pi * r.get_value() ** 3)
        drdt_tracker = ValueTracker(dV_dt / (4 * math.pi * r.get_value() ** 2))

        r_lbl    = MathTex(r"r =",       color=PRIMARY, scale=SCALE_LABEL)
        V_lbl    = MathTex(r"V =",       color=YELLOW,  scale=SCALE_LABEL)
        drdt_lbl = MathTex(r"\frac{dr}{dt} =", color=GREY, scale=SCALE_LABEL)
        dvdt_lbl = MathTex(r"\frac{dV}{dt} = 2.00 = \text{const}",
                           color=GREY, scale=SCALE_ANNOT)

        r_num    = DecimalNumber(r_tracker,    num_decimal_places=2,
                                 color=PRIMARY, scale=SCALE_LABEL)
        V_num    = DecimalNumber(V_tracker,    num_decimal_places=2,
                                 color=YELLOW,  scale=SCALE_LABEL)
        drdt_num = DecimalNumber(drdt_tracker, num_decimal_places=3,
                                 color=GREY,    scale=SCALE_LABEL)

        # Position readouts on the right side
        r_lbl.move_to(4.0, 1.5);    r_num.move_to(5.2, 1.5)
        V_lbl.move_to(4.0, 0.5);    V_num.move_to(5.2, 0.5)
        drdt_lbl.move_to(3.8, -0.5); drdt_num.move_to(5.2, -0.5)
        dvdt_lbl.move_to(4.0, -1.5)

        self.add(r_lbl, r_num, V_lbl, V_num, drdt_lbl, drdt_num, dvdt_lbl)
        self.play(
            AnimationGroup(
                FadeIn(r_lbl,    run_time=0.4),
                FadeIn(r_num,    run_time=0.4),
                FadeIn(V_lbl,    run_time=0.4),
                FadeIn(V_num,    run_time=0.4),
                FadeIn(drdt_lbl, run_time=0.4),
                FadeIn(drdt_num, run_time=0.4),
                FadeIn(dvdt_lbl, run_time=0.4),
                lag_ratio=0.15,
            )
        )

        # ── Inflate: drive r from 0.4 → 2.0 ─────────────────────
        self.section("inflate")
        r_end = 2.0
        V_end = (4 / 3) * math.pi * r_end ** 2
        drdt_end = dV_dt / (4 * math.pi * r_end ** 2)

        self.play(
            AnimationGroup(
                ChangeValue(r,            r_end,    run_time=6.0, rate_func=linear),
                ChangeValue(V_tracker,    V_end,    run_time=6.0, rate_func=linear),
                ChangeValue(drdt_tracker, drdt_end, run_time=6.0, rate_func=linear),
                lag_ratio=0.0,
            )
        )

        payoff = MathTex(
            r"\frac{dr}{dt} = \frac{dV/dt}{4\pi r^2} \searrow \text{ as } r \nearrow",
            color=PRIMARY, scale=SCALE_ANNOT,
        )
        place_in_zone(payoff, ZONE_BOTTOM)
        self.add(payoff)
        self.play(Write(payoff, run_time=1.2))
        self.wait(2.5)
