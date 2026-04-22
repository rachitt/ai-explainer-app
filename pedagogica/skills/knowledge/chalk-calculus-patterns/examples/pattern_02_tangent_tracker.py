"""Pattern 02 — Tangent line tracker.

A dot and tangent line sweep along y = x² driven by a ValueTracker.
Slope readout updates every frame via always_redraw.
"""
import math
from chalk import (
    Scene, Axes, plot_function, Dot, Line, MathTex,
    FadeIn, ChangeValue,
    ValueTracker, DecimalNumber, always_redraw,
    BLUE, YELLOW, PRIMARY, GREY,
    SCALE_DISPLAY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)
from chalk.rate_funcs import linear


class TangentTracker(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Tangent line tracker: } y = x^2",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        self.section("setup")
        ax = Axes(x_range=(-0.5, 4.5), y_range=(-1.0, 17.0),
                  width=7.5, height=5.5, x_step=1.0, y_step=4.0, color=GREY)
        f   = lambda x: x ** 2
        f_p = lambda x: 2.0 * x

        graph = plot_function(ax, f, color=BLUE, stroke_width=3.0)
        self.add(ax, graph)
        self.play(FadeIn(ax, run_time=0.6))
        self.play(FadeIn(graph, run_time=1.2))

        self.section("sweep")
        x = ValueTracker(0.0)
        half_len = 1.2  # tangent line half-length in world units

        dot = always_redraw(
            lambda: Dot(point=ax.to_point(x.get_value(), f(x.get_value())),
                        radius=0.13, color=YELLOW)
        )

        def make_tangent():
            xv = x.get_value()
            m  = f_p(xv)
            # Line from (wx - ½, wy - m·½) to (wx + ½, wy + m·½)
            wx, wy = ax.to_point(xv, f(xv))
            # World-unit slope: m_world = m * (height/y_span) / (width/x_span)
            # Use data-unit slope directly; line endpoints in world coords
            y_scale = ax._h / (ax.y_range[1] - ax.y_range[0])
            x_scale = ax._w / (ax.x_range[1] - ax.x_range[0])
            m_world = m * y_scale / x_scale
            angle   = math.atan2(m_world, 1.0)
            dx = half_len * math.cos(angle)
            dy = half_len * math.sin(angle)
            return Line((wx - dx, wy - dy), (wx + dx, wy + dy),
                        color=PRIMARY, stroke_width=2.5)

        tangent = always_redraw(make_tangent)

        slope_tracker = ValueTracker(0.0)
        slope_disp = always_redraw(
            lambda: MathTex(
                rf"f'(x) = {f_p(x.get_value()):.2f}",
                color=PRIMARY, scale=SCALE_LABEL,
            ).move_to(0.0, -3.1)
        )

        self.add(dot, tangent, slope_disp)
        self.play(FadeIn(dot, run_time=0.3))

        self.play(ChangeValue(x, 4.0, run_time=5.0, rate_func=linear))
        self.wait(2.0)
