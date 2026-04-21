"""Pattern 08 — Function transformation (shift/scale).

Graph of y=f(x) morphs through vertical shift, horizontal shift, vertical
scale, and horizontal scale. Axes stay fixed; the graph is the only thing
that changes.
"""

from manim import (
    BLUE,
    GRAY,
    GREEN,
    ORANGE,
    RED,
    WHITE,
    YELLOW,
    UP,
    Axes,
    Create,
    ReplacementTransform,
    Scene,
    Text,
)


class FunctionTransformation(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 6, 1],
            x_length=7,
            y_length=4.2,
            tips=False,
            axis_config={"color": GRAY},
        )
        label = Text("y = f(x) = x²", font_size=30, color=WHITE).to_edge(UP)

        f0 = lambda x: x**2  # noqa: E731
        f1 = lambda x: x**2 + 1.5  # noqa: E731
        f2 = lambda x: (x - 1) ** 2 + 1.5  # noqa: E731
        f3 = lambda x: 0.5 * (x - 1) ** 2 + 1.5  # noqa: E731
        f4 = lambda x: 0.5 * (2 * (x - 1)) ** 2 + 1.5  # noqa: E731

        g = ax.plot(f0, color=BLUE, x_range=[-2.5, 2.5])

        self.play(Create(ax))
        self.play(Create(g), Create(label))
        self.wait(0.3)

        for fn, col, text in (
            (f1, GREEN, "y = f(x) + 1.5"),
            (f2, YELLOW, "y = f(x − 1) + 1.5"),
            (f3, ORANGE, "y = 0.5·f(x − 1) + 1.5"),
            (f4, RED, "y = 0.5·f(2(x − 1)) + 1.5"),
        ):
            new_g = ax.plot(fn, color=col, x_range=[-2.5, 2.5])
            new_label = Text(text, font_size=30, color=WHITE).to_edge(UP)
            self.play(ReplacementTransform(g, new_g), ReplacementTransform(label, new_label), run_time=1.5)
            g, label = new_g, new_label
            self.wait(0.3)
        self.wait(0.3)
