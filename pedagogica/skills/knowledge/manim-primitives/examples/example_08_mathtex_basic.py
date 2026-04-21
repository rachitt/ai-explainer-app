"""MathTex basic: render a formula with Write.

REQUIRES LaTeX INSTALL (pdflatex + dvisvgm + standalone.cls). On macOS:

    brew install --cask basictex
    eval "$(/usr/libexec/path_helper)"
    sudo tlmgr update --self
    sudo tlmgr install standalone preview doublestroke relsize everysel \
        ms rsfs setspace tipa wasy wasysym xcolor

See `manim-debugging` entry `latex-missing-package` for the catalog of
common LaTeX-side errors.
"""

from manim import MathTex, Scene, Write


class MathTexBasic(Scene):
    def construct(self) -> None:
        eq = MathTex(r"\frac{d}{dx}\,x^2 = 2x", font_size=72)
        self.play(Write(eq))
        self.wait(0.5)
