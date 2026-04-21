"""Explicit key_map on TransformMatchingTex.

REQUIRES LaTeX.

Scenario: source has `ax^2 + bx + c` and target has `ax^2 + bx`. Default
matching will pair the common parts automatically; key_map below is redundant
here but demonstrates the syntax for cases where default matching picks up
the wrong pairs (typically when two substrings share glyphs, e.g., `2x` →
`3x` vs `2x` → `2x^2`).

Expected frame: `ax^2 + bx + c = 0` morphs into `ax^2 + bx = -c`; the pieces
move cleanly because the key_map pins `c` → `-c`.
"""

from manim import MathTex, Scene, TransformMatchingTex, Write


class KeyMapTransform(Scene):
    def construct(self) -> None:
        src = MathTex(r"ax^2", r"+", r"bx", r"+", r"c", r"=", r"0", font_size=60)
        tgt = MathTex(r"ax^2", r"+", r"bx", r"=", r"-c", font_size=60)

        self.play(Write(src))
        self.wait(0.3)
        self.play(
            TransformMatchingTex(src, tgt, key_map={r"c": r"-c"}),
            run_time=1.5,
        )
        self.wait(0.5)
