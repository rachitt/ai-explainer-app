"""Pattern 05 — ε-δ limit window.

For f(x) = x² at x₀=2, L=4: shrink ε → δ shrinks automatically (δ = √(4+ε) - 2).
Two always_redraw bands show the constraint visually.
"""
import math
from chalk import (
    Scene, Axes, plot_function, Line, Rectangle, Dot, MathTex,
    FadeIn, Write, ChangeValue,
    ValueTracker, always_redraw,
    BLUE, YELLOW, GREEN, PRIMARY, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)
from chalk.rate_funcs import smooth
from chalk.mobject import VMobject
import numpy as np


class EpsilonDelta(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\varepsilon\text{-}\delta\text{ limit: } \lim_{x\to 2} x^2 = 4",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        self.section("setup")
        ax = Axes(x_range=(-0.3, 4.3), y_range=(-0.3, 9.3),
                  width=7.5, height=5.5, x_step=1.0, y_step=2.0, color=GREY)
        f = lambda x: x ** 2
        x0, L = 2.0, 4.0
        graph = plot_function(ax, f, color=BLUE, stroke_width=3.0)

        # Limit point dot
        limit_dot = Dot(point=ax.to_point(x0, L), radius=0.12, color=YELLOW)

        self.add(ax, graph, limit_dot)
        self.play(FadeIn(ax, run_time=0.6))
        self.play(FadeIn(graph, run_time=1.0))
        self.play(FadeIn(limit_dot, run_time=0.3))

        self.section("bands")
        eps = ValueTracker(2.0)

        def delta_from_eps(e):
            # For f(x)=x², f⁻¹(L+ε) - x₀  (positive side, symmetric approx)
            return math.sqrt(L + e) - x0

        def eps_band():
            # Horizontal band: L-ε to L+ε full width of axes
            e = eps.get_value()
            wx_l = -ax._w / 2
            wx_r =  ax._w / 2
            wy_bot = ax.to_point(x0, L - e)[1]
            wy_top = ax.to_point(x0, L + e)[1]
            h = wy_top - wy_bot
            m = VMobject(
                fill_color=YELLOW, fill_opacity=0.20,
                stroke_color=YELLOW, stroke_width=1.0, stroke_opacity=0.7,
            )
            # Build a filled rectangle as 4 cubic segments
            pts = []
            corners = [(wx_l, wy_bot), (wx_r, wy_bot), (wx_r, wy_top), (wx_l, wy_top)]
            for i in range(4):
                a = corners[i]
                b = corners[(i + 1) % 4]
                d = ((b[0]-a[0])/3, (b[1]-a[1])/3)
                pts.extend([a, (a[0]+d[0], a[1]+d[1]),
                             (a[0]+2*d[0], a[1]+2*d[1]), b])
            m.points = np.array(pts, dtype=float)
            return m

        def delta_band():
            d = delta_from_eps(eps.get_value())
            wx_l = ax.to_point(x0 - d, 0.0)[0]
            wx_r = ax.to_point(x0 + d, 0.0)[0]
            wy_bot = -ax._h / 2
            wy_top =  ax._h / 2
            m = VMobject(
                fill_color=GREEN, fill_opacity=0.20,
                stroke_color=GREEN, stroke_width=1.0, stroke_opacity=0.7,
            )
            pts = []
            corners = [(wx_l, wy_bot), (wx_r, wy_bot), (wx_r, wy_top), (wx_l, wy_top)]
            for i in range(4):
                a = corners[i]
                b = corners[(i + 1) % 4]
                d3 = ((b[0]-a[0])/3, (b[1]-a[1])/3)
                pts.extend([a, (a[0]+d3[0], a[1]+d3[1]),
                             (a[0]+2*d3[0], a[1]+2*d3[1]), b])
            m.points = np.array(pts, dtype=float)
            return m

        eps_rect   = always_redraw(eps_band)
        delta_rect = always_redraw(delta_band)

        eps_lbl   = MathTex(r"\varepsilon\text{-window}", color=YELLOW, scale=SCALE_ANNOT)
        delta_lbl = MathTex(r"\delta\text{-window}", color=GREEN,  scale=SCALE_ANNOT)
        eps_lbl.move_to(-5.0, 2.0)
        delta_lbl.move_to(-5.0, 0.5)

        self.add(eps_rect, delta_rect, eps_lbl, delta_lbl)
        self.play(FadeIn(eps_rect, run_time=0.5), FadeIn(delta_rect, run_time=0.5))
        self.play(FadeIn(eps_lbl, run_time=0.4), FadeIn(delta_lbl, run_time=0.4))
        self.wait(0.5)

        # Shrink ε → bands shrink together
        self.play(ChangeValue(eps, 0.5, run_time=3.5, rate_func=smooth))
        self.wait(0.8)
        self.play(ChangeValue(eps, 0.15, run_time=3.0, rate_func=smooth))

        payoff = MathTex(r"\forall\,\varepsilon > 0\;\exists\,\delta > 0 \text{ s.t. } |x-2|<\delta \Rightarrow |x^2-4|<\varepsilon",
                         color=PRIMARY, scale=SCALE_ANNOT)
        place_in_zone(payoff, ZONE_BOTTOM)
        self.add(payoff)
        self.play(Write(payoff, run_time=1.5))
        self.wait(2.5)
