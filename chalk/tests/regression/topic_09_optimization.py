"""Topic 09 — Optimization: box with maximum volume.

Square sheet 10×10. Cut corners of size x → box volume V(x) = x(10-2x)².
Maximum at x = 5/3 ≈ 1.667.  V-curve + moving dot + maximum marker.
"""
import math
from chalk import (
    Scene, Axes, plot_function, Line, Dot, MathTex,
    FadeIn, Write, ChangeValue,
    ValueTracker, DecimalNumber, always_redraw,
    BLUE, YELLOW, GREEN, PRIMARY, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)
from chalk.rate_funcs import smooth

X_OPT = 5.0 / 3.0


def V(x: float) -> float:
    return x * (10 - 2 * x) ** 2


class Optimization(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Optimization: max volume box from } 10{\times}10 \text{ sheet}",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        self.section("axes")
        ax = Axes(x_range=(-0.2, 5.2), y_range=(-5.0, 105.0),
                  width=6.5, height=5.0, x_step=1.0, y_step=20.0, color=GREY)
        graph = plot_function(ax, V, x_start=0.0, x_end=5.0, color=BLUE, stroke_width=3.0)

        # Optimal point marker
        opt_wx, opt_wy = ax.to_point(X_OPT, V(X_OPT))
        opt_dot = Dot(point=(opt_wx, opt_wy), radius=0.12, color=YELLOW)
        opt_line = Line(
            start=ax.to_point(X_OPT, 0.0),
            end=ax.to_point(X_OPT, V(X_OPT)),
            color=YELLOW, stroke_width=1.5,
        )

        x_lbl = MathTex(r"x", color=GREY, scale=SCALE_ANNOT)
        V_lbl = MathTex(r"V(x)", color=BLUE, scale=SCALE_ANNOT)
        x_lbl.move_to(ax.to_point(5.2, -10.0)[0], ax.to_point(5.2, -10.0)[1])
        V_lbl.move_to(-3.0, 2.8)

        self.add(ax, graph)
        self.play(FadeIn(ax, run_time=0.6), FadeIn(graph, run_time=1.0))

        self.section("moving_dot")
        x_track = ValueTracker(0.3)

        def tracker_dot():
            xv = x_track.get_value()
            return Dot(point=ax.to_point(xv, V(xv)), radius=0.10, color=GREEN)

        moving = always_redraw(tracker_dot)
        self.add(moving)
        self.play(FadeIn(moving, run_time=0.3))
        self.play(ChangeValue(x_track, 5.0, run_time=3.0, rate_func=smooth))
        self.wait(0.4)
        self.play(ChangeValue(x_track, X_OPT, run_time=2.0, rate_func=smooth))

        self.add(opt_dot, opt_line)
        self.play(FadeIn(opt_dot, run_time=0.4), FadeIn(opt_line, run_time=0.4))

        self.section("payoff")
        payoff = MathTex(
            r"V'(x)=0 \;\Rightarrow\; x = \tfrac{5}{3} \approx 1.67,\quad V_{\max} \approx 74.1",
            color=PRIMARY, scale=SCALE_ANNOT,
        )
        place_in_zone(payoff, ZONE_BOTTOM)
        self.add(payoff)
        self.play(Write(payoff, run_time=1.5))
        self.wait(2.0)
