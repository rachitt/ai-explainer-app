"""Axes + plot_function: draw a parabola y = x².

Demonstrates: Axes constructor, plot_function, FadeIn on VGroup.
"""
from chalk import (
    Scene, Axes, plot_function, MathTex,
    FadeIn,
    BLUE, GREY, PRIMARY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER,
    place_in_zone, next_to,
)
from chalk.vgroup import VGroup


class AxesPlot(Scene):
    def construct(self):
        lbl = MathTex(r"y = x^2", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        ax = Axes(
            x_range=(-2.5, 2.5),
            y_range=(-0.5, 6.5),
            width=8.0,
            height=5.0,
            x_step=1.0,
            y_step=2.0,
            color=GREY,
        )
        graph = plot_function(ax, lambda x: x**2, color=BLUE, stroke_width=3.0)

        # Label at the curve's top-right
        graph_lbl = MathTex(r"y = x^2", color=BLUE, scale=SCALE_LABEL)
        tip_x, tip_y = ax.to_point(2.0, 4.0)
        graph_lbl.move_to(tip_x + 0.5, tip_y + 0.3)

        self.add(ax, graph, graph_lbl)
        self.play(FadeIn(ax, run_time=0.6))
        self.play(FadeIn(graph, run_time=1.2))
        self.play(FadeIn(graph_lbl, run_time=0.4))
        self.wait(2.0)
