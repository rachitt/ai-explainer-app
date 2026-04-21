"""Indexed MathTex with per-term colours.

REQUIRES LaTeX.

Expected frame: `d/dx (x^2 + 3x) = 2x + 3` with:
  - operators (=, +, parens) in GRAY
  - x^2 and its derivative 2x in YELLOW
  - 3x and its derivative 3 in BLUE
  - d/dx operator in RED
"""

from manim import BLUE, GRAY, RED, YELLOW, MathTex, Scene, Write


class ColorCodedSubstrings(Scene):
    def construct(self) -> None:
        # Index layout:
        # 0: d/dx   1: (   2: x^2   3: +   4: 3x   5: )   6: =   7: 2x   8: +   9: 3
        eq = MathTex(
            r"\frac{d}{dx}",
            r"\left(",
            r"x^2",
            r"+",
            r"3x",
            r"\right)",
            r"=",
            r"2x",
            r"+",
            r"3",
            font_size=64,
        )
        eq[0].set_color(RED)
        for i in (1, 3, 5, 6, 8):
            eq[i].set_color(GRAY)
        eq[2].set_color(YELLOW)   # x^2
        eq[7].set_color(YELLOW)   # 2x
        eq[4].set_color(BLUE)     # 3x
        eq[9].set_color(BLUE)     # 3

        self.play(Write(eq))
        self.wait(0.5)
