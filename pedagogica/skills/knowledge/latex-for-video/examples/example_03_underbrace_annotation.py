"""Underbrace annotations, both LaTeX-native and Manim-Brace paths.

REQUIRES LaTeX.

Expected frame: Equation `f'(x) = lim_{h→0} (f(x+h)-f(x))/h` with:
  - LaTeX-native \\underbrace under `lim` reading "limit"
  - Manim Brace under the difference-quotient fraction, label "difference quotient"
    appearing after the equation is written (stepped reveal).
"""

from manim import DOWN, GrowFromCenter, Brace, MathTex, Scene, Text, Write


class UnderbraceAnnotation(Scene):
    def construct(self) -> None:
        # Path A: LaTeX-native \underbrace embedded in the equation
        eq = MathTex(
            r"f'(x)",
            r"=",
            r"\underbrace{\lim_{h \to 0}}_{\text{limit}}",
            r"\frac{f(x+h) - f(x)}{h}",
            font_size=56,
        )
        self.play(Write(eq))
        self.wait(0.3)

        # Path B: Manim Brace on the difference quotient, with stepped reveal
        brace = Brace(eq[3], DOWN, buff=0.15)
        brace_label = Text("difference quotient", font_size=28).next_to(brace, DOWN, buff=0.12)

        self.play(GrowFromCenter(brace), Write(brace_label))
        self.wait(0.5)
