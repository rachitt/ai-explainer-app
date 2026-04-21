"""TransformMatchingTex: morph an equation by shared LaTeX substrings.

The source and target share the literal substring "= 2x"; TransformMatchingTex
keeps that piece anchored and animates only what differs. This is the right
primitive for "edit one term of an equation" — unlike a plain Transform
(which interpolates every glyph), the shared part sits still and the viewer's
eye follows only the change.

REQUIRES LaTeX INSTALL (see example_08).
"""

from manim import MathTex, Scene, TransformMatchingTex, Write


class MathTexTransformMatchingTex(Scene):
    def construct(self) -> None:
        src = MathTex(r"\frac{d}{dx}", r"x^2", r"=", r"2x", font_size=72)
        tgt = MathTex(r"\frac{d}{dx}", r"x^3", r"=", r"3x^2", font_size=72)
        self.play(Write(src))
        self.wait(0.5)
        self.play(TransformMatchingTex(src, tgt), run_time=1.5)
        self.wait(0.5)
