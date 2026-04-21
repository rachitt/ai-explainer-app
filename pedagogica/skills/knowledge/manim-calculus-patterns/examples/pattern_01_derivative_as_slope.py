"""Pattern 01 — Derivative as slope (secant → tangent).

Secant line between two points on y=x^2. Sliding the second point toward the
first collapses the secant into the tangent at the first point. Slope
readout updates in sync.

REQUIRES LaTeX (MathTex in the readout).
"""

from manim import (
    BLUE,
    GRAY,
    RED,
    WHITE,
    YELLOW,
    Axes,
    Create,
    Dot,
    Line,
    MathTex,
    Scene,
    ValueTracker,
    Write,
    always_redraw,
)


class DerivativeAsSlope(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[-0.5, 3.5, 1],
            y_range=[-1, 9, 2],
            x_length=7,
            y_length=4,
            tips=False,
            axis_config={"color": GRAY},
        )
        f = lambda x: x**2  # noqa: E731
        parabola = ax.plot(f, color=BLUE, x_range=[-0.5, 3.2])

        x0 = 1.0
        h = ValueTracker(1.5)  # second point at x0 + h

        dot_a = Dot(ax.c2p(x0, f(x0)), color=YELLOW, radius=0.1)
        dot_b = always_redraw(
            lambda: Dot(ax.c2p(x0 + h.get_value(), f(x0 + h.get_value())), color=YELLOW, radius=0.1)
        )

        def secant_line() -> Line:
            x1 = x0 + h.get_value()
            p1 = ax.c2p(x0 - 0.3, f(x0) - 0.3 * (f(x1) - f(x0)) / (x1 - x0))
            p2 = ax.c2p(x1 + 0.3, f(x1) + 0.3 * (f(x1) - f(x0)) / (x1 - x0))
            return Line(p1, p2, color=RED, stroke_width=4)

        secant = always_redraw(secant_line)

        def slope_num() -> MathTex:
            x1 = x0 + h.get_value()
            m = (f(x1) - f(x0)) / (x1 - x0)
            return MathTex(rf"\text{{slope}} = {m:.2f}", color=WHITE, font_size=40).to_edge("UP")

        readout = always_redraw(slope_num)

        self.play(Create(ax))
        self.play(Create(parabola), run_time=1.5)
        self.play(Create(dot_a), Create(dot_b))
        self.add(secant, readout)
        self.play(Write(MathTex(r"f(x)=x^2", font_size=36).to_corner("UR")))
        self.wait(0.5)
        # Drive h toward 0 — tangent emerges
        self.play(h.animate.set_value(0.05), run_time=4.0)
        self.wait(0.5)
        secant.clear_updaters()
        dot_b.clear_updaters()
        readout.clear_updaters()
        self.wait(0.3)
