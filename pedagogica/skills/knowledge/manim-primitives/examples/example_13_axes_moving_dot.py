"""Dot moving along a graph via MoveAlongPath.

Contrast with example 15, which uses a ValueTracker + always_redraw to the
same visual effect. MoveAlongPath is simpler for a one-shot sweep; the
tracker pattern is needed when multiple derived objects (tangent, slope
readout) must update in sync with the parameter.
"""

from manim import BLUE, YELLOW, Axes, Create, Dot, MoveAlongPath, Scene


class AxesMovingDot(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[-1, 4, 1],
            y_range=[-1, 9, 2],
            x_length=7,
            y_length=4,
            tips=False,
        )
        parabola = ax.plot(lambda x: x**2, color=BLUE, x_range=[-1, 3])
        dot = Dot(ax.c2p(-1, 1), color=YELLOW, radius=0.12)

        self.play(Create(ax))
        self.play(Create(parabola), run_time=1.5)
        self.play(Create(dot))
        self.play(MoveAlongPath(dot, parabola), run_time=3.0)
        self.wait(0.5)
