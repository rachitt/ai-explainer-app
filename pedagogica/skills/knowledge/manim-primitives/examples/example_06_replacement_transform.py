"""ReplacementTransform: circle → square, then operate on the square.

After ReplacementTransform, `circle` has been removed from the scene and the
on-screen object is bound to `square`. This is the safe default when the
morph result will be manipulated further (shifted, re-coloured, transformed
again).
"""

from manim import BLUE, GREEN, RED, UP, Circle, Create, ReplacementTransform, Scene, Square


class ReplacementTransformDemo(Scene):
    def construct(self) -> None:
        circle = Circle(radius=1.5, color=BLUE)
        square = Square(side_length=3, color=RED)
        self.play(Create(circle))
        self.wait(0.3)
        self.play(ReplacementTransform(circle, square), run_time=1.5)
        # Now work with the *square*, not the original reference.
        self.play(square.animate.shift(UP * 1.5).set_color(GREEN))
        self.wait(0.5)
