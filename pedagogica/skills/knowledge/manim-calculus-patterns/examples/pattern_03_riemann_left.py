"""Pattern 03 — Left-Riemann sum, N=8 bars under y=x^2 on [0, 3]."""

from manim import (
    BLUE,
    GRAY,
    GREEN,
    WHITE,
    UP,
    AnimationGroup,
    Axes,
    Create,
    DrawBorderThenFill,
    Rectangle,
    Scene,
    Text,
    VGroup,
)


class RiemannLeft(Scene):
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

        N = 8
        a, b = 0.0, 3.0
        dx = (b - a) / N
        bars = VGroup()
        for i in range(N):
            xl = a + i * dx
            h = f(xl)
            bottom_left = ax.c2p(xl, 0)
            top_right = ax.c2p(xl + dx, h)
            width = top_right[0] - bottom_left[0]
            height = top_right[1] - bottom_left[1]
            rect = Rectangle(
                width=width,
                height=height,
                color=GREEN,
                fill_color=GREEN,
                fill_opacity=0.5,
                stroke_width=2,
            )
            rect.move_to(
                [
                    (bottom_left[0] + top_right[0]) / 2,
                    (bottom_left[1] + top_right[1]) / 2,
                    0,
                ]
            )
            bars.add(rect)

        label = Text(f"Left-Riemann, N = {N}", font_size=32, color=WHITE).to_edge(UP)

        self.play(Create(ax))
        self.play(Create(curve), run_time=1.5)
        self.play(
            AnimationGroup(*[DrawBorderThenFill(b) for b in bars], lag_ratio=0.08),
            run_time=2.0,
        )
        self.play(Create(label))
        self.wait(0.5)
