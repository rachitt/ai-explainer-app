"""counter_demo: DecimalNumber counting 0 → 100 over 3 seconds."""
from chalk import (
    Scene, VGroup, MathTex, FadeIn, ChangeValue,
    ValueTracker, DecimalNumber,
    PRIMARY, YELLOW, SCALE_DISPLAY, SCALE_BODY,
    ZONE_TOP, ZONE_CENTER,
    place_in_zone,
)
from chalk.rate_funcs import linear


class CounterDemo(Scene):
    def construct(self):
        title = MathTex(r"\text{Counting: } 0 \to 100", color=PRIMARY, scale=SCALE_BODY)
        place_in_zone(title, ZONE_TOP)
        self.add(title)
        self.play(FadeIn(title, run_time=0.6))

        t = ValueTracker(0.0)
        counter = DecimalNumber(t, num_decimal_places=0, color=YELLOW, scale=SCALE_DISPLAY)
        place_in_zone(counter, ZONE_CENTER)
        self.add(counter)

        self.play(ChangeValue(t, 100.0, run_time=3.0, rate_func=linear))
        self.wait(1.5)
