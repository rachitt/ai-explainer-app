"""ValueTracker + DecimalNumber counter.

Demonstrates: ValueTracker, DecimalNumber, ChangeValue, linear rate.
"""
from chalk import (
    Scene, MathTex, DecimalNumber, ValueTracker,
    FadeIn, ChangeValue,
    PRIMARY, GREY,
    SCALE_DISPLAY, SCALE_BODY,
    ZONE_TOP, ZONE_CENTER,
    place_in_zone,
)
from chalk.rate_funcs import linear


class ValueTrackerDecimal(Scene):
    def construct(self):
        lbl = MathTex(r"\text{ValueTracker + DecimalNumber}", color=GREY, scale=SCALE_BODY)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        tracker = ValueTracker(0.0)
        counter = DecimalNumber(tracker, num_decimal_places=0,
                                color=PRIMARY, scale=SCALE_DISPLAY)
        place_in_zone(counter, ZONE_CENTER)
        self.add(counter)

        # Animate 0 → 100 over 4 seconds
        self.play(ChangeValue(tracker, 100.0, run_time=4.0, rate_func=linear))
        self.wait(2.0)
