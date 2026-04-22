"""Pattern 07 — FTC area accumulator.

Shaded region under f(t)=t grows as x sweeps from 0 to 4.
A second axes below plots A(x) = x²/2 (the antiderivative).
Key: precompute A(x) array; never call integration inside always_redraw.
"""
import numpy as np
from chalk import (
    Scene, Axes, plot_function, Line, Dot, MathTex,
    FadeIn, Write, ChangeValue,
    ValueTracker, always_redraw,
    BLUE, GREEN, YELLOW, PRIMARY, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP,
    place_in_zone, next_to,
)
from chalk.mobject import VMobject
from chalk.rate_funcs import linear


class FTCAccumulator(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"A(x) = \int_0^x t\,dt \;\Rightarrow\; A'(x) = x",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        self.section("setup")
        f   = lambda t: t
        A   = lambda x: x ** 2 / 2.0
        a, b = 0.0, 4.0

        # Top axes: f(t) = t
        ax1 = Axes(x_range=(-0.3, 4.5), y_range=(-0.3, 4.5),
                   width=7.5, height=3.0, x_step=1.0, y_step=1.0, color=GREY)
        ax1.shift(0.0, 1.5)

        graph1 = plot_function(ax1, f, color=BLUE, stroke_width=3.0)

        # Bottom axes: A(x)
        ax2 = Axes(x_range=(-0.3, 4.5), y_range=(-0.3, 8.5),
                   width=7.5, height=3.0, x_step=1.0, y_step=2.0, color=GREY)
        ax2.shift(0.0, -2.2)

        graph2 = plot_function(ax2, A, color=PRIMARY, stroke_width=3.0)

        self.add(ax1, graph1, ax2, graph2)
        self.play(FadeIn(ax1, run_time=0.5), FadeIn(graph1, run_time=0.8))
        self.play(FadeIn(ax2, run_time=0.5), FadeIn(graph2, run_time=0.8))

        self.section("sweep")
        x = ValueTracker(a)

        # Sweep line on top axes
        sweep_line = always_redraw(lambda: Line(
            ax1.to_point(x.get_value(), 0.0),
            ax1.to_point(x.get_value(), f(x.get_value())),
            color=YELLOW, stroke_width=2.0,
        ))

        # Shaded area: rebuild as filled polygon each frame (N=30 samples)
        def make_area():
            xv = max(x.get_value(), 0.001)
            xs = np.linspace(a, xv, 30)
            pts = []
            # Bottom edge left to right
            for xi in xs:
                wx, wy = ax1.to_point(xi, 0.0)
                pts.append((wx, wy))
            # Top edge right to left (follow curve)
            for xi in reversed(xs):
                wx, wy = ax1.to_point(xi, f(xi))
                pts.append((wx, wy))
            # Build as closed VMobject
            m = VMobject(fill_color=GREEN, fill_opacity=0.35,
                         stroke_color=GREEN, stroke_width=0.0)
            chain = []
            for i in range(len(pts) - 1):
                pa, pb = pts[i], pts[i+1]
                d = ((pb[0]-pa[0])/3, (pb[1]-pa[1])/3)
                chain.extend([pa, (pa[0]+d[0], pa[1]+d[1]),
                               (pa[0]+2*d[0], pa[1]+2*d[1]), pb])
            m.points = np.array(chain, dtype=float)
            return m

        area = always_redraw(make_area)

        # Dot on A(x) curve
        accum_dot = always_redraw(
            lambda: Dot(point=ax2.to_point(x.get_value(), A(x.get_value())),
                        radius=0.12, color=YELLOW)
        )

        self.add(area, sweep_line, accum_dot)
        self.play(FadeIn(sweep_line, run_time=0.3))
        self.play(FadeIn(area, run_time=0.4))
        self.play(FadeIn(accum_dot, run_time=0.3))

        self.play(ChangeValue(x, b, run_time=5.0, rate_func=linear))
        self.wait(0.5)

        payoff = MathTex(r"A'(x) = f(x)", color=PRIMARY, scale=SCALE_LABEL)
        payoff.move_to(4.5, -1.5)
        self.add(payoff)
        self.play(Write(payoff, run_time=0.8))
        self.wait(2.5)
