"""BEFORE — MathTex given a non-raw string; Python mangles \\f as form feed.

The call either SyntaxErrors on load (on some Python versions) or compiles
but produces bizarre LaTeX source with control characters.

Catalog: mathtex-raw-string-missing.

REQUIRES LaTeX to actually observe the failure, but the Python-level hazard
(mangled escapes) is real without LaTeX too.
"""

from manim import MathTex, Scene, Write


class RawStringMissingBefore(Scene):
    def construct(self) -> None:
        eq = MathTex("\frac{d}{dx}")   # noqa: W605 — deliberate buggy original
        self.play(Write(eq))
        self.wait(0.3)
