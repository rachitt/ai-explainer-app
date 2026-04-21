"""AFTER — minimum edit: .get_graph → .plot."""

from manim import BLUE, Axes, Create, Scene


class GetGraphAfter(Scene):
    def construct(self) -> None:
        ax = Axes(x_range=[-1, 4, 1], y_range=[-1, 9, 2], x_length=7, y_length=4)
        curve = ax.plot(lambda x: x**2, color=BLUE)
        self.play(Create(ax))
        self.play(Create(curve))
        self.wait(0.3)
