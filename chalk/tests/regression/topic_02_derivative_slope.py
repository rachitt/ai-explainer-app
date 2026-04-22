"""Pattern 01 — Derivative as slope (secant → tangent).

Drive h → 0.01: two dots on y=x², secant line rotates into tangent.
Slope readout converges to f'(x₀) = 2x₀.
"""
from chalk import (
    Scene, Axes, plot_function, Dot, Line, MathTex,
    FadeIn, Write, ChangeValue,
    ValueTracker, DecimalNumber, always_redraw,
    BLUE, YELLOW, PRIMARY, GREY,
    SCALE_DISPLAY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
    place_in_zone, next_to,
)
from chalk.rate_funcs import smooth


class DerivativeAsSlope(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Derivative as slope: } y = x^2",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        # ── Setup axes and curve ─────────────────────────────────
        self.section("setup")
        ax = Axes(x_range=(-0.5, 3.5), y_range=(-0.5, 9.5),
                  width=7.5, height=5.5, x_step=1.0, y_step=2.0, color=GREY)
        f    = lambda x: x ** 2
        f_p  = lambda x: 2 * x
        x0 = 1.5

        graph = plot_function(ax, f, color=BLUE, stroke_width=3.0)
        self.add(ax, graph)
        self.play(FadeIn(ax, run_time=0.6))
        self.play(FadeIn(graph, run_time=1.2))

        # ── Secant: drive h → 0.01 ───────────────────────────────
        self.section("secant_sweep")
        h = ValueTracker(1.5)

        dot_a = always_redraw(
            lambda: Dot(point=ax.to_point(x0, f(x0)), radius=0.12, color=YELLOW)
        )
        dot_b = always_redraw(
            lambda: Dot(point=ax.to_point(x0 + h.get_value(),
                                          f(x0 + h.get_value())),
                        radius=0.12, color=YELLOW)
        )
        secant = always_redraw(lambda: Line(
            ax.to_point(x0, f(x0)),
            ax.to_point(x0 + h.get_value(), f(x0 + h.get_value())),
            color=PRIMARY, stroke_width=2.0,
        ))
        slope_val = always_redraw(
            lambda: DecimalNumber(
                ValueTracker((f(x0 + max(h.get_value(), 0.01)) - f(x0)) /
                             max(h.get_value(), 0.01)),
                num_decimal_places=2,
                color=PRIMARY,
                scale=SCALE_DISPLAY,
            ).move_to(*ax.to_point(2.8, -0.5))
        )
        slope_lbl = MathTex(r"\text{slope} =", color=PRIMARY, scale=SCALE_LABEL)
        slope_lbl.move_to(ax.to_point(1.5, -0.5)[0] - 0.8, ax.to_point(1.5, -0.5)[1])

        self.add(dot_a, dot_b, secant, slope_lbl, slope_val)
        self.play(FadeIn(dot_a, run_time=0.4), FadeIn(dot_b, run_time=0.4),
                  FadeIn(secant, run_time=0.5))
        self.play(FadeIn(slope_lbl, run_time=0.4), FadeIn(slope_val, run_time=0.4))

        # Drive h to 0.01 — secant becomes tangent
        self.play(ChangeValue(h, 0.01, run_time=3.5, rate_func=smooth))
        self.wait(0.5)

        # Annotate the limit
        deriv_lbl = MathTex(r"f'(1.5) = 3.0", color=YELLOW, scale=SCALE_LABEL)
        place_in_zone(deriv_lbl, ZONE_BOTTOM)
        self.add(deriv_lbl)
        self.play(Write(deriv_lbl, run_time=0.9))
        self.wait(2.5)
