"""VGroup: axes + graph + label move as one unit.

Without grouping, shifting the axes would leave the graph behind.  A VGroup
binds its children's transforms, so any .animate on the group applies to all
constituents.
"""

from manim import BLUE, LEFT, UP, Axes, Create, Scene, Text, VGroup


class VGroupCoordination(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[-1, 4, 1],
            y_range=[-1, 9, 2],
            x_length=6,
            y_length=3.5,
            tips=False,
        )
        parabola = ax.plot(lambda x: x**2, color=BLUE, x_range=[-1, 3])
        label = Text("y = x^2", font_size=32).next_to(parabola, UP + LEFT, buff=0.2)

        axes_group = VGroup(ax, parabola, label)

        self.play(Create(ax))
        self.play(Create(parabola), run_time=1.5)
        self.add(label)
        self.wait(0.3)
        # Shift the whole group — graph and label follow the axes.
        self.play(axes_group.animate.shift(LEFT * 2).scale(0.8), run_time=1.5)
        self.wait(0.3)
