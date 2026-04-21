"""Pattern 05 — ε-δ limit window for f(x)=x^2 near x=1, L=1.

δ-band on x-axis, ε-band on y-axis; as ε shrinks we display the matching δ
(here δ = √(1+ε) − 1 ≈ ε/2 for small ε). Shows that for every ε a δ exists.

REQUIRES LaTeX (MathTex labels).
"""

import math

from manim import (
    BLUE,
    GRAY,
    GREEN,
    RED,
    WHITE,
    UP,
    Axes,
    Create,
    DashedLine,
    MathTex,
    Rectangle,
    Scene,
    ValueTracker,
    always_redraw,
)


class EpsilonDelta(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[0, 2, 0.5],
            y_range=[0, 4, 1],
            x_length=6,
            y_length=4,
            tips=False,
            axis_config={"color": GRAY},
        )
        f = lambda x: x**2  # noqa: E731
        curve = ax.plot(f, color=BLUE, x_range=[0, 1.8])

        a, L = 1.0, 1.0
        eps = ValueTracker(1.0)

        def delta_for(e: float) -> float:
            # For f(x)=x^2, L=1: |x^2 - 1| < e  <=>  x in (sqrt(1-e), sqrt(1+e))
            return min(math.sqrt(1 + e) - 1, 1 - math.sqrt(max(1e-4, 1 - e)))

        def eps_band() -> Rectangle:
            e = eps.get_value()
            bl = ax.c2p(0, L - e)
            tr = ax.c2p(2, L + e)
            w = tr[0] - bl[0]
            h = tr[1] - bl[1]
            r = Rectangle(width=w, height=h, color=RED, fill_color=RED, fill_opacity=0.18, stroke_width=0)
            r.move_to([(bl[0] + tr[0]) / 2, (bl[1] + tr[1]) / 2, 0])
            return r

        def delta_band() -> Rectangle:
            d = delta_for(eps.get_value())
            bl = ax.c2p(a - d, 0)
            tr = ax.c2p(a + d, 4)
            w = tr[0] - bl[0]
            h = tr[1] - bl[1]
            r = Rectangle(width=w, height=h, color=GREEN, fill_color=GREEN, fill_opacity=0.18, stroke_width=0)
            r.move_to([(bl[0] + tr[0]) / 2, (bl[1] + tr[1]) / 2, 0])
            return r

        eps_rect = always_redraw(eps_band)
        delta_rect = always_redraw(delta_band)
        vline = DashedLine(ax.c2p(a, 0), ax.c2p(a, L), color=WHITE, stroke_width=2)
        hline = DashedLine(ax.c2p(0, L), ax.c2p(a, L), color=WHITE, stroke_width=2)

        readout = always_redraw(
            lambda: MathTex(
                rf"\varepsilon = {eps.get_value():.2f} \ \Rightarrow\  \delta \approx {delta_for(eps.get_value()):.2f}",
                color=WHITE,
                font_size=36,
            ).to_edge(UP)
        )

        self.play(Create(ax))
        self.play(Create(curve), run_time=1.2)
        self.play(Create(vline), Create(hline))
        self.add(eps_rect, delta_rect, readout)
        self.wait(0.5)
        self.play(eps.animate.set_value(0.5), run_time=2.5)
        self.play(eps.animate.set_value(0.15), run_time=2.5)
        eps_rect.clear_updaters()
        delta_rect.clear_updaters()
        readout.clear_updaters()
        self.wait(0.3)
