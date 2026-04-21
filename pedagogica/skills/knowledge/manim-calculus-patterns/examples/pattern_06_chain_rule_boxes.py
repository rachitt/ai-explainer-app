"""Pattern 06 — Chain rule as nested boxes.

x → [ g ] → g(x) → [ f ] → f(g(x))

Then arrows labelled with local derivatives show f'(g(x))·g'(x)·dx.

REQUIRES LaTeX (MathTex on every label).
"""

from manim import (
    BLUE,
    GREEN,
    WHITE,
    YELLOW,
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Create,
    FadeIn,
    MathTex,
    Rectangle,
    Scene,
    Write,
)


class ChainRuleBoxes(Scene):
    def construct(self) -> None:
        inner = Rectangle(width=1.8, height=1.2, color=GREEN).shift(LEFT * 1.2)
        outer = Rectangle(width=1.8, height=1.2, color=BLUE).shift(RIGHT * 1.8)

        g_label = MathTex("g", color=GREEN, font_size=48).move_to(inner.get_center())
        f_label = MathTex("f", color=BLUE, font_size=48).move_to(outer.get_center())

        x_in = MathTex("x", font_size=40, color=WHITE).next_to(inner, LEFT, buff=0.6)
        gx = MathTex("g(x)", font_size=36, color=WHITE).move_to(
            (inner.get_right() + outer.get_left()) / 2 + UP * 0.6
        )
        fgx = MathTex("f(g(x))", font_size=40, color=WHITE).next_to(outer, RIGHT, buff=0.6)

        arr1 = Arrow(x_in.get_right(), inner.get_left(), buff=0.1, color=WHITE)
        arr2 = Arrow(inner.get_right(), outer.get_left(), buff=0.1, color=WHITE)
        arr3 = Arrow(outer.get_right(), fgx.get_left(), buff=0.1, color=WHITE)

        self.play(FadeIn(x_in))
        self.play(Create(arr1), Create(inner), Write(g_label))
        self.play(Create(arr2), FadeIn(gx))
        self.play(Create(outer), Write(f_label))
        self.play(Create(arr3), FadeIn(fgx))
        self.wait(0.5)

        # Derivative overlay
        d_x = MathTex("dx", font_size=32, color=YELLOW).next_to(arr1, DOWN, buff=0.15)
        d_gx = MathTex(r"g'(x)\,dx", font_size=32, color=YELLOW).next_to(arr2, DOWN, buff=0.15)
        d_fgx = MathTex(r"f'(g(x))\,g'(x)\,dx", font_size=32, color=YELLOW).next_to(arr3, DOWN, buff=0.15)

        self.play(FadeIn(d_x))
        self.play(FadeIn(d_gx))
        self.play(FadeIn(d_fgx))
        self.wait(0.5)

        conclusion = MathTex(
            r"\frac{d}{dx}\,f(g(x)) = f'(g(x))\,g'(x)",
            font_size=40,
            color=WHITE,
        ).to_edge(DOWN)
        self.play(Write(conclusion))
        self.wait(0.5)
