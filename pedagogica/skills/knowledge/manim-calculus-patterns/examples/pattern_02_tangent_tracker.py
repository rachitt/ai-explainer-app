"""Pattern 02 — Tangent line tracker (no-LaTeX path).

Moving dot + tangent line driven by a single ValueTracker(x). Slope readout
via Text + f-string so the pattern runs without a LaTeX install; in
production, swap for MathTex + TransformMatchingTex per latex-for-video.
"""

from manim import (
    BLUE,
    GRAY,
    RED,
    WHITE,
    YELLOW,
    UP,
    Axes,
    Create,
    Dot,
    Line,
    Scene,
    Text,
    ValueTracker,
    always_redraw,
)


class TangentTracker(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[-1, 4, 1],
            y_range=[-1, 9, 2],
            x_length=7,
            y_length=4,
            tips=False,
            axis_config={"color": GRAY},
        )
        f = lambda x: x**2  # noqa: E731
        df = lambda x: 2 * x  # noqa: E731
        parabola = ax.plot(f, color=BLUE, x_range=[-1, 3])

        x = ValueTracker(-0.8)

        dot = always_redraw(
            lambda: Dot(ax.c2p(x.get_value(), f(x.get_value())), color=YELLOW, radius=0.12)
        )

        def tangent_line() -> Line:
            x0 = x.get_value()
            m = df(x0)
            dx = 1.0
            p1 = ax.c2p(x0 - dx, f(x0) - m * dx)
            p2 = ax.c2p(x0 + dx, f(x0) + m * dx)
            return Line(p1, p2, color=RED, stroke_width=4)

        tangent = always_redraw(tangent_line)
        readout = always_redraw(
            lambda: Text(
                f"slope at x = {x.get_value():.2f}  →  {df(x.get_value()):.2f}",
                font_size=32,
                color=WHITE,
            ).to_edge(UP)
        )

        self.play(Create(ax))
        self.play(Create(parabola), run_time=1.5)
        self.add(dot, tangent, readout)
        self.play(x.animate.set_value(2.8), run_time=4.0)
        dot.clear_updaters()
        tangent.clear_updaters()
        readout.clear_updaters()
        self.wait(0.3)
