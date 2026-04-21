"""Axes with get_graph_label — a label that follows the curve.

`get_graph_label` places a label near the graph with automatic anchoring;
if the graph is transformed, the label moves with it via grouping.

REQUIRES LaTeX INSTALL for the math label (MathTex under the hood).
"""

from manim import BLUE, RIGHT, UP, Axes, Create, Scene, Write


class AxesGraphLabel(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[-1, 4, 1],
            y_range=[-1, 9, 2],
            x_length=7,
            y_length=4,
            tips=False,
        )
        parabola = ax.plot(lambda x: x**2, color=BLUE, x_range=[-1, 3])
        label = ax.get_graph_label(parabola, label="x^2", x_val=2.5, direction=UP + RIGHT)

        self.play(Create(ax))
        self.play(Create(parabola), run_time=1.5)
        self.play(Write(label))
        self.wait(0.5)
