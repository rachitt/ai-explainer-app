"""Runnable Manim example for the text-plus-visual framing.

Beat: Riemann sum → integral. LEFT column grows a three-line derivation;
RIGHT column shrinks rectangles until they become a smooth filled area.

Layout obeys scene-composition §5.3:
  - LEFT text top-anchored at (-3.5, +3.0), growing downward
  - RIGHT visual centred at (+3.5, 0), in a 5×4 bounding box
  - Optional guide separator at x = 0

Ship check: renders with `manim -qm example_03_text_plus_visual.py RiemannToIntegral`
on Manim Community 0.19.x. Visual review required at PR merge.

Not a test; `tests/test_examples_render.py` (Phase 1 week 3) will import this module
and assert frame_count > 0 after render.
"""
from manim import (
    Axes,
    Create,
    FadeIn,
    FadeOut,
    ManimColor,
    MathTex,
    Line,
    Scene,
    Transform,
    VGroup,
    Write,
    DOWN,
)

BG = ManimColor("#0E1116")
PRIMARY = ManimColor("#E8EAED")
VARIABLE = ManimColor("#4FC3F7")
RESULT = ManimColor("#FFD54F")
ANNOT = ManimColor("#9AA0A6")


class RiemannToIntegral(Scene):
    def construct(self) -> None:
        self.camera.background_color = BG

        # optional separator at x = 0
        separator = Line(
            start=[0, -3.2, 0], end=[0, 3.0, 0], stroke_width=1, color=ANNOT
        )
        self.add(separator)

        # --- LEFT column: text, top-anchored at (-3.5, +3.0), growing downward ---
        line_1 = MathTex(
            r"\sum_{i=1}^{n} f(x_i)\,\Delta x",
            font_size=36,
        ).set_color(PRIMARY)
        line_1.move_to([-3.5, 2.3, 0])

        line_2 = MathTex(
            r"\lim_{n \to \infty}\sum_{i=1}^{n} f(x_i)\,\Delta x",
            font_size=36,
        ).set_color(PRIMARY)
        line_2.move_to([-3.5, 0.8, 0])

        line_3 = MathTex(
            r"\int_{a}^{b} f(x)\, dx",
            font_size=48,
        ).set_color(RESULT)
        line_3.move_to([-3.5, -0.8, 0])

        # --- RIGHT column: axes + parabola + rectangles in a 5×4 bounding box ---
        axes = Axes(
            x_range=[0, 2, 0.5],
            y_range=[0, 4, 1],
            x_length=4.5,
            y_length=3.6,
            axis_config={"color": ANNOT, "stroke_width": 2},
            tips=False,
        ).move_to([3.5, 0, 0])

        parabola = axes.plot(lambda x: x ** 2, x_range=[0, 2], color=VARIABLE)

        n_coarse = 6
        n_fine = 24
        rects_coarse = axes.get_riemann_rectangles(
            parabola, x_range=[0, 2], dx=2 / n_coarse, color=VARIABLE, stroke_width=1
        )
        rects_fine = axes.get_riemann_rectangles(
            parabola, x_range=[0, 2], dx=2 / n_fine, color=VARIABLE, stroke_width=0.5
        )
        filled_area = axes.get_area(parabola, x_range=[0, 2], color=RESULT, opacity=0.5)

        right_group = VGroup(axes, parabola)

        # --- Animation: the two columns advance in lock-step ---

        # anchored to narration words (illustrative indices; real values come from Script.markers)
        self.play(Create(axes), run_time=0.6)
        self.play(Create(parabola), run_time=0.9)
        self.wait(0.15)

        # beat 1: show sum
        self.play(FadeIn(rects_coarse, shift=DOWN * 0.1), Write(line_1), run_time=1.2)
        self.wait(0.4)  # authored micro-pause on "Δx."

        # beat 2: take n → ∞
        self.play(Transform(rects_coarse, rects_fine), Write(line_2), run_time=1.4)
        self.wait(0.4)  # authored micro-pause

        # beat 3: land on the integral
        self.play(
            FadeOut(rects_coarse),
            FadeIn(filled_area),
            Write(line_3),
            run_time=1.6,
        )
        self.wait(0.8)  # authored landing pause — TTS is saying "…is the integral."
