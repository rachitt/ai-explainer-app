"""ValueTracker driving a tangent line through add_updater.

When the derived object has substructure that shouldn't be re-allocated every
frame, use .add_updater and mutate the mobject in place rather than
always_redraw (which re-runs the constructor 30 times/sec).
"""

from manim import BLUE, RED, Axes, Create, Line, Scene, ValueTracker


class ValueTrackerUpdater(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[-1, 4, 1],
            y_range=[-1, 9, 2],
            x_length=7,
            y_length=4,
            tips=False,
        )
        parabola = ax.plot(lambda x: x**2, color=BLUE, x_range=[-1, 3])
        x = ValueTracker(0.2)

        def tangent() -> Line:
            x0 = x.get_value()
            slope = 2 * x0
            p1 = ax.c2p(x0 - 1, x0**2 - slope * 1)
            p2 = ax.c2p(x0 + 1, x0**2 + slope * 1)
            return Line(p1, p2, color=RED, stroke_width=4)

        tan = tangent()

        def update_tangent(m: Line) -> None:
            m.become(tangent())

        tan.add_updater(update_tangent)

        self.play(Create(ax))
        self.play(Create(parabola), run_time=1.5)
        self.add(tan)
        self.play(x.animate.set_value(2.5), run_time=3.0)
        tan.clear_updaters()
        self.wait(0.3)
