"""BEFORE — Pre-0.18 API: ax.get_graph exists. On 0.19 this AttributeErrors.

Catalog: axes-get-graph-renamed.
"""

from manim import BLUE, Axes, Create, Scene


class GetGraphBefore(Scene):
    def construct(self) -> None:
        ax = Axes(x_range=[-1, 4, 1], y_range=[-1, 9, 2], x_length=7, y_length=4)
        curve = ax.get_graph(lambda x: x**2, color=BLUE)   # <-- fails on 0.19
        self.play(Create(ax))
        self.play(Create(curve))
        self.wait(0.3)
