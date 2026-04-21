"""BEFORE — Dot placed at scene coords [2, 4, 0] but meant to sit at data (2, 4).

No stderr — the scene renders, but the dot floats offscreen because the axes
have x_range=[0, 10] with x_length=7, so data coord (2, 4) maps to scene
coord (-1.6, 0.8, 0), not (2, 4, 0).

Catalog: c2p-on-raw-coordinates.
"""

from manim import BLUE, YELLOW, Axes, Create, Dot, Scene


class MissingC2PBefore(Scene):
    def construct(self) -> None:
        ax = Axes(x_range=[0, 10, 2], y_range=[0, 10, 2], x_length=7, y_length=4)
        parabola = ax.plot(lambda x: x, color=BLUE, x_range=[0, 10])
        dot = Dot([2, 4, 0], color=YELLOW, radius=0.12)   # raw scene coords
        self.play(Create(ax))
        self.play(Create(parabola))
        self.play(Create(dot))
        self.wait(0.3)
