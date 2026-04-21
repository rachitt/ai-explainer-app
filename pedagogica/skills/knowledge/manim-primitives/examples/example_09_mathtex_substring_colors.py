"""MathTex with indexed substrings coloured independently.

Passing a list of strings to MathTex gives each substring an index, so they
can be coloured, transformed, or moved independently. This is the highest-
leverage MathTex pattern — used everywhere in `latex-for-video`.

REQUIRES LaTeX INSTALL (see example_08).
"""

from manim import BLUE, YELLOW, MathTex, Scene, Write


class MathTexSubstringColors(Scene):
    def construct(self) -> None:
        # Four indexed substrings: [0] "\frac{d}{dx}"  [1] "x^2"  [2] "="  [3] "2x"
        eq = MathTex(r"\frac{d}{dx}", r"x^2", r"=", r"2x", font_size=72)
        eq[1].set_color(YELLOW)   # x^2 in yellow
        eq[3].set_color(BLUE)     # 2x in blue
        self.play(Write(eq))
        self.wait(0.5)
