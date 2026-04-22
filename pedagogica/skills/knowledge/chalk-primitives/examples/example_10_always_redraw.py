"""always_redraw: a Dot that tracks a ValueTracker on an Axes.

Demonstrates: always_redraw factory pattern, ChangeValue driving a dot position.
"""
from chalk import (
    Scene, Axes, plot_function, Dot, MathTex,
    FadeIn, ChangeValue,
    ValueTracker, always_redraw,
    BLUE, YELLOW, GREY,
    SCALE_ANNOT,
    ZONE_TOP,
    place_in_zone,
)
from chalk.rate_funcs import linear


class AlwaysRedrawDot(Scene):
    def construct(self):
        lbl = MathTex(r"\text{always\_redraw: dot follows x}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        ax = Axes(
            x_range=(-0.5, 4.5),
            y_range=(-0.5, 20.5),
            width=7.5,
            height=5.5,
            x_step=1.0,
            y_step=5.0,
            color=GREY,
        )
        f = lambda x: x ** 2
        graph = plot_function(ax, f, color=BLUE, stroke_width=2.5)

        self.add(ax, graph)
        self.play(FadeIn(ax, run_time=0.5), FadeIn(graph, run_time=1.0))

        x = ValueTracker(0.0)

        # always_redraw rebuilds this Dot every frame from the tracker
        dot = always_redraw(
            lambda: Dot(
                point=ax.to_point(x.get_value(), f(x.get_value())),
                radius=0.14,
                color=YELLOW,
            )
        )
        self.add(dot)
        self.play(FadeIn(dot, run_time=0.3))

        # Sweep x from 0 to 4; dot follows the parabola
        self.play(ChangeValue(x, 4.0, run_time=4.0, rate_func=linear))
        self.wait(1.5)
