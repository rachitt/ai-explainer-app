"""Three-line aligned derivation, one step at a time.

REQUIRES LaTeX.

Expected frame: (x+1)^2 expanded over three lines. First line is written in;
second line appears below; third line appears below that. No line shifts its
position as new lines appear.
"""

from manim import LEFT, UP, MathTex, Scene, Write


class DerivationStepped(Scene):
    def construct(self) -> None:
        derivation = MathTex(
            r"(x+1)^2 &= (x+1)(x+1) \\",
            r"        &= x^2 + x + x + 1 \\",
            r"        &= x^2 + 2x + 1",
            font_size=48,
        ).to_edge(UP + LEFT)

        for line in derivation:
            self.play(Write(line), run_time=1.0)
            self.wait(0.3)
        self.wait(0.5)
