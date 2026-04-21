"""Transform: circle morphs into a square.

After `Transform(circle, square)`, the on-screen object is still referenced as
`circle` — it now *looks* like a square. Use ReplacementTransform instead if
you want to manipulate the result under the name `square`.
"""

from manim import BLUE, RED, Circle, Create, Scene, Square, Transform


class TransformCircleToSquare(Scene):
    def construct(self) -> None:
        circle = Circle(radius=1.5, color=BLUE)
        square = Square(side_length=3, color=RED)
        self.play(Create(circle))
        self.wait(0.3)
        self.play(Transform(circle, square), run_time=1.5)
        self.wait(0.5)
