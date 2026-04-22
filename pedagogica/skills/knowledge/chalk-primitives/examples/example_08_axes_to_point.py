"""ax.to_point(x, y) — map data coordinates to world coordinates.

Demonstrates: to_point, Dot placement on axes, the c2p-equivalent pattern.
"""
from chalk import (
    Scene, Axes, plot_function, Dot, MathTex,
    FadeIn, LaggedStart,
    BLUE, YELLOW, PRIMARY, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP,
    place_in_zone, next_to,
)


class AxesToPoint(Scene):
    def construct(self):
        lbl = MathTex(r"\text{ax.to\_point(x, y)}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        ax = Axes(
            x_range=(-0.5, 3.5),
            y_range=(-0.5, 10.5),
            width=7.0,
            height=5.5,
            x_step=1.0,
            y_step=2.0,
            color=GREY,
        )
        graph = plot_function(ax, lambda x: x**2, color=BLUE, stroke_width=2.5)

        self.add(ax, graph)
        self.play(FadeIn(ax, run_time=0.5), FadeIn(graph, run_time=1.0))

        # Place dots at data coordinates using to_point
        data_points = [(1.0, 1.0), (2.0, 4.0), (3.0, 9.0)]
        dots, labels = [], []
        for dx, dy in data_points:
            wx, wy = ax.to_point(dx, dy)
            d = Dot(point=(wx, wy), radius=0.13, color=YELLOW)
            l = MathTex(rf"({dx:.0f},{dy:.0f})", color=PRIMARY, scale=SCALE_LABEL)
            next_to(l, d, direction="RIGHT", buff=0.15)
            dots.append(d)
            labels.append(l)

        self.add(*dots, *labels)
        self.play(
            LaggedStart(
                *[FadeIn(d, run_time=0.4) for d in dots],
                lag_ratio=0.3,
            )
        )
        self.play(
            LaggedStart(
                *[FadeIn(l, run_time=0.4) for l in labels],
                lag_ratio=0.3,
            )
        )
        self.wait(2.0)
