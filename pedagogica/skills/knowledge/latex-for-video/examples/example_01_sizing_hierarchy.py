"""Font-size hierarchy: hero (72) / running (36) / label (28) side-by-side.

REQUIRES LaTeX.

Expected frame: three MathTex expressions stacked vertically, each in its tier
size so a reviewer can eyeball whether the hero reads from 10 feet away and
the label reads from 2 feet.
"""

from manim import DOWN, MathTex, Scene, VGroup, Write


class SizingHierarchy(Scene):
    def construct(self) -> None:
        hero = MathTex(r"\frac{d}{dx}\,x^2 = 2x", font_size=72)
        running = MathTex(r"f'(1) = 2", font_size=36)
        label = MathTex(r"x \in [0, 3]", font_size=28)

        stack = VGroup(hero, running, label).arrange(DOWN, buff=0.6)

        self.play(Write(hero))
        self.play(Write(running))
        self.play(Write(label))
        self.wait(0.5)
