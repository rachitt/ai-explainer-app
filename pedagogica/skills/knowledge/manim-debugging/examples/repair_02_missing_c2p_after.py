"""AFTER — dot now uses ax.c2p for data-space placement."""

from manim import BLUE, YELLOW, Axes, Create, Dot, Scene


class MissingC2PAfter(Scene):
    def construct(self) -> None:
        ax = Axes(x_range=[0, 10, 2], y_range=[0, 10, 2], x_length=7, y_length=4)
        parabola = ax.plot(lambda x: x, color=BLUE, x_range=[0, 10])
        dot = Dot(ax.c2p(2, 4), color=YELLOW, radius=0.12)   # data coords
        self.play(Create(ax))
        self.play(Create(parabola))
        self.play(Create(dot))
        self.wait(0.3)
