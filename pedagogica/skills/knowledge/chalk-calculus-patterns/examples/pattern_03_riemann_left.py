"""Pattern 03 — Left-Riemann sum.

N=8 left-endpoint rectangles under y = x² on [0, 3].
Heights and positions computed in world coords via ax.to_point.
"""
from chalk import (
    Scene, Axes, plot_function, Rectangle, MathTex,
    FadeIn, Write, LaggedStart,
    BLUE, GREEN, GREY,
    SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)


class RiemannLeft(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Left-Riemann sum: } y = x^2 \text{ on } [0,3]",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        self.section("setup")
        ax = Axes(x_range=(-0.3, 3.5), y_range=(-0.3, 9.5),
                  width=7.5, height=5.5, x_step=1.0, y_step=2.0, color=GREY)
        f = lambda x: x ** 2
        graph = plot_function(ax, f, color=BLUE, stroke_width=3.0)
        self.add(ax, graph)
        self.play(FadeIn(ax, run_time=0.6))
        self.play(FadeIn(graph, run_time=1.0))

        self.section("rectangles")
        N = 8
        a, b = 0.0, 3.0
        dx = (b - a) / N

        rects = []
        for i in range(N):
            xi = a + i * dx
            # World coords: anchor = bottom-left of bar
            wx_left,  wy_bot = ax.to_point(xi, 0.0)
            wx_right, wy_top = ax.to_point(xi + dx, f(xi))  # left-endpoint height
            w = wx_right - wx_left
            h = wy_top - wy_bot
            r = Rectangle(
                width=w, height=h,
                fill_color=GREEN, fill_opacity=0.4,
                color=GREEN, stroke_width=1.5,
            )
            # Place bottom-left corner at (wx_left, wy_bot)
            r.shift(wx_left + w / 2, wy_bot + h / 2)
            rects.append(r)

        self.add(*rects)
        self.play(
            LaggedStart(*[FadeIn(r, run_time=0.5) for r in rects], lag_ratio=0.08)
        )

        self.section("label")
        sum_lbl = MathTex(
            r"\sum_{i=0}^{7} f(x_i)\,\Delta x \approx \int_0^3 x^2\,dx",
            color=GREEN, scale=SCALE_LABEL,
        )
        place_in_zone(sum_lbl, ZONE_BOTTOM)
        self.add(sum_lbl)
        self.play(Write(sum_lbl, run_time=1.2))
        self.wait(2.5)
