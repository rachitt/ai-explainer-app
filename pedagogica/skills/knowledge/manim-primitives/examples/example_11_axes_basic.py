"""Axes + plot + c2p dot placement.

Three things at once: construct Axes with explicit lengths; plot f(x)=x^2;
place a Dot at the data coordinate (2, 4) via ax.c2p. Raw scene coordinates
would not track the axes if they were later rescaled; c2p-placed objects do.
"""

from manim import BLUE, YELLOW, Axes, Create, Dot, Scene


class AxesBasic(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[-1, 4, 1],
            y_range=[-1, 9, 2],
            x_length=7,
            y_length=4,
            tips=False,
        )
        parabola = ax.plot(lambda x: x**2, color=BLUE, x_range=[-1, 3])
        dot = Dot(ax.c2p(2, 4), color=YELLOW, radius=0.12)

        self.play(Create(ax))
        self.play(Create(parabola), run_time=1.5)
        self.play(Create(dot))
        self.wait(0.5)
