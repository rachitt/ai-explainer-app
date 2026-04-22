"""Pattern 04 — Riemann → integral limit.

N steps 4 → 8 → 16 → 64. FadeOut old rects, FadeIn new. Label Σ → ∫ via TransformMatchingTex.
"""
from chalk import (
    Scene, Axes, plot_function, Rectangle, MathTex,
    FadeIn, FadeOut, Write,
    LaggedStart, AnimationGroup,
    TransformMatchingTex,
    BLUE, GREEN, PRIMARY, GREY,
    SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)
from chalk.vgroup import VGroup


def make_rects(ax, N, f, a=0.0, b=3.0):
    dx = (b - a) / N
    rects = []
    for i in range(N):
        xi = a + i * dx
        wx_l, wy_b = ax.to_point(xi, 0.0)
        wx_r, wy_t = ax.to_point(xi + dx, f(xi))
        w = wx_r - wx_l
        h = wy_t - wy_b
        r = Rectangle(
            width=w, height=h,
            fill_color=GREEN, fill_opacity=0.4,
            color=GREEN, stroke_width=max(0.5, 1.5 * 8 / N),
        )
        r.shift(wx_l + w / 2, wy_b + h / 2)
        rects.append(r)
    return rects


class RiemannToIntegral(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"N \to \infty: \sum \to \int", color=GREY, scale=SCALE_ANNOT)
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

        sum_eq = MathTex(r"\sum_{i=1}^{N} f(x_i)\,\Delta x",
                         color=GREEN, scale=SCALE_LABEL)
        place_in_zone(sum_eq, ZONE_BOTTOM)
        self.add(sum_eq)
        self.play(Write(sum_eq, run_time=0.9))

        # ── Step through N values ─────────────────────────────────
        self.section("n_steps")
        current_rects = make_rects(ax, 4, f)
        self.add(*current_rects)
        self.play(LaggedStart(*[FadeIn(r, run_time=0.5) for r in current_rects],
                               lag_ratio=0.12))

        for N in [8, 16, 64]:
            new_rects = make_rects(ax, N, f)
            self.add(*new_rects)
            self.play(
                AnimationGroup(
                    *[FadeOut(r, run_time=0.4) for r in current_rects],
                    lag_ratio=0.0,
                )
            )
            self.play(
                LaggedStart(*[FadeIn(r, run_time=0.3) for r in new_rects],
                             lag_ratio=0.02)
            )
            current_rects = new_rects
            self.wait(0.4)

        # ── Morph label Σ → ∫ ────────────────────────────────────
        self.section("label_morph")
        int_eq = MathTex(r"\int_0^3 f(x)\,dx", color=PRIMARY, scale=SCALE_LABEL)
        place_in_zone(int_eq, ZONE_BOTTOM)
        self.play(TransformMatchingTex(sum_eq, int_eq, run_time=1.5))
        self.wait(2.5)
