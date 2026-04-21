"""ValueTracker + Text counter via always_redraw.

The canonical "counter ticking from 0 to N" pattern. `DecimalNumber` is the
more idiomatic Manim primitive for numeric readouts, but it requires LaTeX.
For the no-LaTeX path, `always_redraw` on a Text built from f-string
formatting works identically — the lambda runs every frame and `self.add`
pins the result.
"""

from manim import Scene, Text, ValueTracker, always_redraw


class ValueTrackerBasic(Scene):
    def construct(self) -> None:
        x = ValueTracker(0)
        counter = always_redraw(lambda: Text(f"{x.get_value():.2f}", font_size=96))
        self.add(counter)

        self.play(x.animate.set_value(10), run_time=3.0)
        self.wait(0.3)
