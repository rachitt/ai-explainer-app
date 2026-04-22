"""Topic 01 — Derivative as rate of change.

Secant line from x=1 to x=1+h; h shrinks 1.5→0.1, average rate → 2.
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


class DerivativeAsRate(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Derivative as rate of change: } f(x)=x^2",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        self.section("axes")
        ax = Axes(x_range=(-0.3, 3.3), y_range=(-0.3, 9.3),
                  width=7.0, height=5.0, x_step=1.0, y_step=2.0, color=GREY)
        f = lambda x: x ** 2
        x0 = 1.0
        graph = plot_function(ax, f, color=BLUE, stroke_width=3.0)
        p0_dot = Dot(point=ax.to_point(x0, f(x0)), radius=0.10, color=YELLOW)
        self.add(ax, graph, p0_dot)
        self.play(FadeIn(ax, run_time=0.6), FadeIn(graph, run_time=0.9))
        self.play(FadeIn(p0_dot, run_time=0.3))

        self.section("secant")
        h = ValueTracker(1.5)

        def secant():
            hv = h.get_value()
            x1 = x0 + hv
            y0, y1 = f(x0), f(x1)
            wx0, wy0 = ax.to_point(x0 - 0.3, y0 - 0.3 * (y1 - y0) / hv)
            wx1, wy1 = ax.to_point(x1 + 0.3, y1 + 0.3 * (y1 - y0) / hv)
            return Line(start=(wx0, wy0), end=(wx1, wy1),
                        color=GREEN, stroke_width=2.5)

        def p1_dot_mob():
            hv = h.get_value()
            return Dot(point=ax.to_point(x0 + hv, f(x0 + hv)),
                       radius=0.10, color=GREEN)

        sec_line = always_redraw(secant)
        p1_dot  = always_redraw(p1_dot_mob)

        # Rate-of-change readout
        rate_val = always_redraw(
            lambda: DecimalNumber(
                ValueTracker((f(x0 + h.get_value()) - f(x0)) / h.get_value()),
                num_decimal_places=3, color=GREEN, scale=SCALE_LABEL,
            )
        )
        rate_lbl = MathTex(r"\frac{\Delta y}{\Delta x} =", color=GREEN, scale=SCALE_LABEL)
        rate_lbl.move_to(3.8, 1.5)
        rate_val.move_to(5.4, 1.5)

        self.add(sec_line, p1_dot, rate_lbl, rate_val)
        self.play(FadeIn(sec_line, run_time=0.5), FadeIn(p1_dot, run_time=0.3))
        self.play(FadeIn(rate_lbl, run_time=0.3))
        self.wait(0.5)

        self.play(ChangeValue(h, 0.1, run_time=4.0, rate_func=smooth))
        self.wait(0.8)

        self.section("payoff")
        payoff = MathTex(
            r"\lim_{h\to 0}\frac{f(1+h)-f(1)}{h} = 2x\big|_{x=1} = 2",
            color=PRIMARY, scale=SCALE_ANNOT,
        )
        place_in_zone(payoff, ZONE_BOTTOM)
        self.add(payoff)
        self.play(Write(payoff, run_time=1.5))
        self.wait(2.0)
