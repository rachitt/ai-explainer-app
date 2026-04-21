"""Pattern 04 — Riemann → integral (N ∈ {4, 8, 16, 32, 64} → filled area)."""

from manim import (
    BLUE,
    GRAY,
    GREEN,
    WHITE,
    UP,
    Axes,
    Create,
    FadeIn,
    Rectangle,
    ReplacementTransform,
    Scene,
    Text,
    VGroup,
)


class RiemannToIntegral(Scene):
    def construct(self) -> None:
        ax = Axes(
            x_range=[0, 3, 1],
            y_range=[0, 9, 2],
            x_length=7,
            y_length=4,
            tips=False,
            axis_config={"color": GRAY},
        )
        f = lambda x: x**2  # noqa: E731
        curve = ax.plot(f, color=BLUE, x_range=[0, 3])

        def make_bars(N: int) -> VGroup:
            group = VGroup()
            a, b = 0.0, 3.0
            dx = (b - a) / N
            for i in range(N):
                xl = a + i * dx
                h = f(xl)
                bl = ax.c2p(xl, 0)
                tr = ax.c2p(xl + dx, h)
                w, hh = tr[0] - bl[0], tr[1] - bl[1]
                r = Rectangle(
                    width=w,
                    height=hh,
                    color=GREEN,
                    fill_color=GREEN,
                    fill_opacity=0.5,
                    stroke_width=1,
                )
                r.move_to([(bl[0] + tr[0]) / 2, (bl[1] + tr[1]) / 2, 0])
                group.add(r)
            return group

        label = Text("N = 4", font_size=32, color=WHITE).to_edge(UP)
        bars = make_bars(4)

        self.play(Create(ax))
        self.play(Create(curve), run_time=1.5)
        self.play(Create(bars), Create(label))
        self.wait(0.3)

        for N in (8, 16, 32, 64):
            new_bars = make_bars(N)
            new_label = Text(f"N = {N}", font_size=32, color=WHITE).to_edge(UP)
            self.play(
                ReplacementTransform(bars, new_bars),
                ReplacementTransform(label, new_label),
                run_time=1.0,
            )
            bars = new_bars
            label = new_label

        # Morph into the filled area — an ax.get_area is a Polygon-ish mobject.
        area = ax.get_area(curve, x_range=(0, 3), color=GREEN, opacity=0.6)
        final_label = Text("N → ∞  :  area =  ∫₀³ x² dx", font_size=32, color=WHITE).to_edge(UP)
        self.play(FadeIn(area), ReplacementTransform(bars, area), run_time=1.2)
        self.play(ReplacementTransform(label, final_label))
        self.wait(0.5)
