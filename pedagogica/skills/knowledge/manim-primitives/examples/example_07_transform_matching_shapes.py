"""TransformMatchingShapes: morph between two polygons keeping shared parts.

Where a plain Transform interpolates every point, MatchingShapes tries to
identify sub-shapes that exist in both source and target, keeps those anchored,
and fades the non-matching parts in/out.
"""

from manim import BLUE, RED, Create, Scene, Square, Triangle, TransformMatchingShapes


class TransformMatchingShapesDemo(Scene):
    def construct(self) -> None:
        triangle = Triangle(color=BLUE).scale(1.5)
        square = Square(side_length=3, color=RED)
        self.play(Create(triangle))
        self.wait(0.3)
        self.play(TransformMatchingShapes(triangle, square), run_time=1.5)
        self.wait(0.5)
