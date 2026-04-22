"""Topic 10 — Area between curves.

f(x) = x and g(x) = x² on [0, 1].  N=30 strips (midpoint) fade in,
then payoff: ∫₀¹ (x - x²) dx = 1/6.
"""
from chalk import (
    Scene, Axes, plot_function, Rectangle, MathTex,
    FadeIn, Write, LaggedStart,
    BLUE, GREEN, YELLOW, PRIMARY, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)


def make_strips(ax, N=30, a=0.0, b=1.0):
    f = lambda x: x
    g = lambda x: x ** 2
    dx = (b - a) / N
    strips = []
    for i in range(N):
        xm = a + (i + 0.5) * dx
        y_bot = g(xm)
        y_top = f(xm)
        if y_top <= y_bot:
            continue
        wx_l = ax.to_point(a + i * dx, 0.0)[0]
        wx_r = ax.to_point(a + (i + 1) * dx, 0.0)[0]
        wy_b = ax.to_point(xm, y_bot)[1]
        wy_t = ax.to_point(xm, y_top)[1]
        w = wx_r - wx_l
        h = wy_t - wy_b
        r = Rectangle(
            width=w, height=h,
            fill_color=GREEN, fill_opacity=0.5,
            color=GREEN, stroke_width=0.5,
        )
        r.shift(wx_l + w / 2, wy_b + h / 2)
        strips.append(r)
    return strips


class AreaBetweenCurves(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Area between } f(x)=x \text{ and } g(x)=x^2 \text{ on } [0,1]",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        self.section("axes")
        ax = Axes(x_range=(-0.1, 1.4), y_range=(-0.1, 1.4),
                  width=6.0, height=5.5, x_step=0.5, y_step=0.5, color=GREY)
        line_graph = plot_function(ax, lambda x: x,   x_start=0.0, x_end=1.2,
                                   color=BLUE, stroke_width=3.0)
        quad_graph = plot_function(ax, lambda x: x**2, x_start=0.0, x_end=1.2,
                                   color=YELLOW, stroke_width=3.0)

        f_lbl = MathTex(r"f(x)=x",   color=BLUE,   scale=SCALE_ANNOT)
        g_lbl = MathTex(r"g(x)=x^2", color=YELLOW, scale=SCALE_ANNOT)
        f_lbl.move_to(3.5, 2.2)
        g_lbl.move_to(3.5, 0.4)

        self.add(ax, line_graph, quad_graph, f_lbl, g_lbl)
        self.play(FadeIn(ax, run_time=0.6))
        self.play(FadeIn(line_graph, run_time=0.7), FadeIn(quad_graph, run_time=0.7))
        self.play(FadeIn(f_lbl, run_time=0.3), FadeIn(g_lbl, run_time=0.3))

        self.section("strips")
        strips = make_strips(ax, N=30)
        self.add(*strips)
        self.play(
            LaggedStart(*[FadeIn(s, run_time=0.4) for s in strips], lag_ratio=0.05)
        )
        self.wait(0.5)

        self.section("payoff")
        payoff = MathTex(
            r"\int_0^1 (x - x^2)\,dx = \left[\tfrac{x^2}{2}-\tfrac{x^3}{3}\right]_0^1 = \tfrac{1}{6}",
            color=PRIMARY, scale=SCALE_ANNOT,
        )
        place_in_zone(payoff, ZONE_BOTTOM)
        self.add(payoff)
        self.play(Write(payoff, run_time=1.5))
        self.wait(2.0)
