"""Pattern 10 — Related rates: balloon inflating at constant dV/dt.

V = (4/3)πr³ → dV/dt = 4πr² · dr/dt → dr/dt = (dV/dt) / (4πr²).
Show the circle growing; readouts of V, r, dr/dt.
"""

import math

from manim import (
    BLUE,
    GRAY,
    WHITE,
    DOWN,
    UP,
    Circle,
    Create,
    Scene,
    Text,
    ValueTracker,
    VGroup,
    always_redraw,
)


class RelatedRatesBalloon(Scene):
    def construct(self) -> None:
        dVdt = 4.0  # constant inflation rate
        r = ValueTracker(0.5)

        balloon = always_redraw(
            lambda: Circle(
                radius=r.get_value(),
                color=BLUE,
                fill_color=BLUE,
                fill_opacity=0.4,
                stroke_width=3,
            ).move_to([0, -0.5, 0])
        )

        def readouts() -> VGroup:
            rv = r.get_value()
            V = (4 / 3) * math.pi * rv**3
            drdt = dVdt / (4 * math.pi * rv**2)
            return VGroup(
                Text(f"r  = {rv:.2f}", font_size=28, color=WHITE),
                Text(f"V  = {V:.2f}", font_size=28, color=WHITE),
                Text(f"dV/dt = {dVdt:.2f}  (constant)", font_size=28, color=WHITE),
                Text(f"dr/dt = {drdt:.2f}", font_size=28, color=WHITE),
            ).arrange(DOWN, buff=0.15).to_edge(UP)

        readout_group = always_redraw(readouts)

        self.play(Create(balloon))
        self.add(readout_group)
        self.wait(0.3)
        self.play(r.animate.set_value(2.0), run_time=5.0)
        balloon.clear_updaters()
        readout_group.clear_updaters()
        self.wait(0.3)
