"""The minimal hello-world: Write a Text onto the frame."""

from manim import Scene, Text, Write


class WriteText(Scene):
    def construct(self) -> None:
        title = Text("Derivatives", font_size=72)
        self.play(Write(title))
        self.wait(0.5)
