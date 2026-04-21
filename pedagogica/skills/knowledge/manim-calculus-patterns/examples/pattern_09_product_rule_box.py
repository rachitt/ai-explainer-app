"""Pattern 09 — Product rule as a rectangle whose sides grow.

A u×v box. Grow to (u+du)×(v+dv). The new area decomposes into:
  uv (original)  +  v·du (right strip)  +  u·dv (top strip)  +  du·dv (corner, shrinks to 0).
"""

from manim import (
    BLUE,
    GRAY,
    GREEN,
    RED,
    WHITE,
    YELLOW,
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Create,
    FadeIn,
    FadeOut,
    Rectangle,
    Scene,
    Text,
    VGroup,
    Write,
)


class ProductRuleBox(Scene):
    def construct(self) -> None:
        u, v = 3.0, 2.0
        du, dv = 0.8, 0.6

        # Original u×v rectangle
        uv_rect = Rectangle(width=u, height=v, color=BLUE, fill_color=BLUE, fill_opacity=0.4)
        u_label = Text("u", font_size=32, color=WHITE).next_to(uv_rect, DOWN, buff=0.2)
        v_label = Text("v", font_size=32, color=WHITE).next_to(uv_rect, LEFT, buff=0.2)
        uv_inside = Text("u · v", font_size=30, color=WHITE).move_to(uv_rect.get_center())

        self.play(Create(uv_rect))
        self.play(Write(u_label), Write(v_label), Write(uv_inside))
        self.wait(0.3)

        # Right strip of width du, height v
        right_strip = Rectangle(width=du, height=v, color=GREEN, fill_color=GREEN, fill_opacity=0.5)
        right_strip.next_to(uv_rect, RIGHT, buff=0)
        right_label = Text("v · du", font_size=24, color=WHITE).move_to(right_strip.get_center())
        du_label = Text("du", font_size=28, color=GREEN).next_to(right_strip, DOWN, buff=0.2)

        # Top strip of width u, height dv
        top_strip = Rectangle(width=u, height=dv, color=YELLOW, fill_color=YELLOW, fill_opacity=0.5)
        top_strip.next_to(uv_rect, UP, buff=0)
        top_label = Text("u · dv", font_size=24, color=WHITE).move_to(top_strip.get_center())
        dv_label = Text("dv", font_size=28, color=YELLOW).next_to(top_strip, LEFT, buff=0.2)

        # Tiny corner of width du, height dv
        corner = Rectangle(width=du, height=dv, color=RED, fill_color=RED, fill_opacity=0.5)
        corner.next_to(top_strip, RIGHT, buff=0).align_to(right_strip, UP)
        # Just place corner at top-right using explicit coords
        corner.move_to([uv_rect.get_right()[0] + du / 2, uv_rect.get_top()[1] + dv / 2, 0])
        corner_label = Text("du·dv", font_size=20, color=WHITE).move_to(corner.get_center())

        self.play(FadeIn(right_strip), Write(right_label), Write(du_label))
        self.play(FadeIn(top_strip), Write(top_label), Write(dv_label))
        self.play(FadeIn(corner), FadeIn(corner_label))
        self.wait(0.5)

        # Drop the corner — it's second-order small
        self.play(FadeOut(corner), FadeOut(corner_label))
        self.wait(0.3)

        conclusion = Text("d(uv) = v·du + u·dv", font_size=36, color=WHITE).to_edge(DOWN)
        self.play(Write(conclusion))
        self.wait(0.5)
