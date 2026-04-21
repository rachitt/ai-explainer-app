"""ValueTracker + always_redraw: a dot anchored to a graph by x-parameter.

Contrast with example 13 (MoveAlongPath): this pattern scales to several
derived objects — a tangent line, a slope readout, a shaded region under
the curve — all reading the same tracker each frame.
"""

from manim import BLUE, YELLOW, Axes, Create, Dot, Scene, ValueTracker, always_redraw


class ValueTrackerAlwaysRedraw(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[-1, 4, 1],
            y_range=[-1, 9, 2],
            x_length=7,
            y_length=4,
            tips=False,
        )
        parabola = ax.plot(lambda x: x**2, color=BLUE, x_range=[-1, 3])
        x = ValueTracker(-1)
        dot = always_redraw(
            lambda: Dot(ax.c2p(x.get_value(), x.get_value() ** 2), color=YELLOW, radius=0.12)
        )

        self.play(Create(ax))
        self.play(Create(parabola), run_time=1.5)
        self.add(dot)
        self.play(x.animate.set_value(3), run_time=3.0)
        self.wait(0.3)
