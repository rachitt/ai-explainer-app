"""Sequential Write on a VGroup of lines via AnimationGroup + lag_ratio.

Shows the idiomatic way to introduce a list: each line animates in after the
previous, with a small stagger. Avoid a one-shot Write on the whole VGroup —
it feels mechanical.
"""

from manim import DOWN, LEFT, AnimationGroup, Scene, Text, VGroup, Write


class WriteBulletList(Scene):
    def construct(self) -> None:
        lines = VGroup(
            Text("• Rate of change", font_size=36),
            Text("• Slope of a tangent", font_size=36),
            Text("• Limit of a difference quotient", font_size=36),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4)

        self.play(
            AnimationGroup(*[Write(line) for line in lines], lag_ratio=0.5),
            run_time=3.0,
        )
        self.wait(0.5)
