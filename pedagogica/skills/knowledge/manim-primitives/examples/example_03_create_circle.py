"""Create animation on a Circle — outline draws in."""

from manim import BLUE, Circle, Create, Scene


class CreateCircle(Scene):
    def construct(self) -> None:
        circle = Circle(radius=1.5, color=BLUE)
        self.play(Create(circle), run_time=1.5)
        self.wait(0.5)
