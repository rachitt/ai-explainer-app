"""TransformMatchingTex: x^2 → x^3, shared anchors stay put.

REQUIRES LaTeX.

Expected frame: the equation morphs from `d/dx x^2 = 2x` into `d/dx x^3 = 3x^2`;
the `d/dx` and `=` sit still through the transition, only the changed terms
animate.
"""

from manim import MathTex, Scene, TransformMatchingTex, Write


class AlignedTransformation(Scene):
    def construct(self) -> None:
        src = MathTex(r"\frac{d}{dx}", r"x^2", r"=", r"2x", font_size=64)
        tgt = MathTex(r"\frac{d}{dx}", r"x^3", r"=", r"3x^2", font_size=64)

        self.play(Write(src))
        self.wait(0.3)
        self.play(TransformMatchingTex(src, tgt), run_time=1.5)
        self.wait(0.5)
