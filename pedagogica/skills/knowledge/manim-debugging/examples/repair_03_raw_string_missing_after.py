"""AFTER — raw string prefix; LaTeX source is intact."""

from manim import MathTex, Scene, Write


class RawStringMissingAfter(Scene):
    def construct(self) -> None:
        eq = MathTex(r"\frac{d}{dx}")
        self.play(Write(eq))
        self.wait(0.3)
