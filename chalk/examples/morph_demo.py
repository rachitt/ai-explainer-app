"""Morph demo — exercises Transform subpath propagation.

Requires LaTeX (basictex + tlmgr packages listed in workflows/lessons.md).
"""
from chalk import Scene, MathTex, Transform, FadeIn, PRIMARY, SCALE_DISPLAY


class MorphDemo(Scene):
    def construct(self) -> None:
        a = MathTex(r"x^2", color=PRIMARY, scale=SCALE_DISPLAY)
        b = MathTex(r"x^3", color=PRIMARY, scale=SCALE_DISPLAY)
        self.add(a)
        self.play(FadeIn(a, run_time=0.6))
        self.wait(0.8)

        anims = [
            Transform(src, tgt, run_time=1.2)
            for src, tgt in zip(a.submobjects, b.submobjects)
        ]
        self.play(*anims, run_time=1.2)
        self.wait(1.5)
