"""Pattern 07 — FTC area accumulator (no-LaTeX path).

Upper axes: y = f(t) = t with moving vertical line at t=x and shaded area
from a=0 to t=x. Lower axes: the accumulator A(x) = x²/2 plotted as x sweeps.
Dot on the accumulator curve tracks the numeric area.
"""

from manim import (
    BLUE,
    GRAY,
    GREEN,
    RED,
    WHITE,
    YELLOW,
    DOWN,
    UP,
    Axes,
    Create,
    DashedLine,
    Dot,
    Scene,
    Text,
    ValueTracker,
    VGroup,
    always_redraw,
)


class FTCAccumulator(Scene):
    def construct(self) -> None:
        ax_top = Axes(
            x_range=[0, 3, 1],
            y_range=[0, 3.5, 1],
            x_length=6,
            y_length=2.4,
            tips=False,
            axis_config={"color": GRAY},
        ).to_edge(UP, buff=0.8)
        ax_bot = Axes(
            x_range=[0, 3, 1],
            y_range=[0, 5, 1],
            x_length=6,
            y_length=2.4,
            tips=False,
            axis_config={"color": GRAY},
        ).to_edge(DOWN, buff=0.8)

        f = lambda t: t  # noqa: E731  # trivial f so accumulator is x^2/2
        A = lambda x: 0.5 * x**2  # noqa: E731
        curve = ax_top.plot(f, color=BLUE, x_range=[0, 3])
        acc_curve = ax_bot.plot(A, color=YELLOW, x_range=[0, 3])

        label_top = Text("y = t", font_size=24, color=WHITE).next_to(ax_top, UP, buff=0.1)
        label_bot = Text("A(x) = ∫₀ˣ t dt", font_size=24, color=WHITE).next_to(ax_bot, UP, buff=0.1)

        x = ValueTracker(0.01)

        vline = always_redraw(
            lambda: DashedLine(
                ax_top.c2p(x.get_value(), 0),
                ax_top.c2p(x.get_value(), f(x.get_value())),
                color=RED,
                stroke_width=3,
            )
        )
        area = always_redraw(
            lambda: ax_top.get_area(
                curve, x_range=(0, max(x.get_value(), 0.02)), color=GREEN, opacity=0.5
            )
        )
        acc_dot = always_redraw(
            lambda: Dot(ax_bot.c2p(x.get_value(), A(x.get_value())), color=YELLOW, radius=0.1)
        )

        self.play(Create(VGroup(ax_top, ax_bot)))
        self.play(Create(curve), Create(acc_curve), run_time=1.5)
        self.play(Create(label_top), Create(label_bot))
        self.add(vline, area, acc_dot)
        self.wait(0.3)
        self.play(x.animate.set_value(3.0), run_time=4.5)
        vline.clear_updaters()
        area.clear_updaters()
        acc_dot.clear_updaters()
        self.wait(0.3)
