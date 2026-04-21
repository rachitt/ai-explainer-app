"""DrawBorderThenFill on a filled rectangle — outline first, then fill.

Use for solid shapes that should feel deliberately constructed. The canonical
case in calculus scenes is a Riemann-sum bar.
"""

from manim import BLUE, DrawBorderThenFill, Rectangle, Scene


class DrawBorderThenFillBar(Scene):
    def construct(self) -> None:
        bar = Rectangle(
            width=1.5,
            height=3.0,
            color=BLUE,
            fill_color=BLUE,
            fill_opacity=0.5,
            stroke_width=3,
        )
        self.play(DrawBorderThenFill(bar), run_time=1.5)
        self.wait(0.5)
