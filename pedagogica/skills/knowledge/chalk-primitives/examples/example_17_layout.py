"""place_in_zone, next_to, labeled_box, arrow_between.

Demonstrates: all layout helpers in one scene. Never hard-code coordinates.
"""
from chalk import (
    Scene, Circle, MathTex,
    FadeIn,
    PRIMARY, BLUE, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
    place_in_zone, next_to,
)
from chalk.layout import labeled_box, arrow_between


class LayoutDemo(Scene):
    def construct(self):
        top_lbl = MathTex(r"\text{Layout helpers}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(top_lbl, ZONE_TOP)
        self.add(top_lbl)
        self.play(FadeIn(top_lbl, run_time=0.4))

        # labeled_box: auto-sized rectangle around text
        box_a, lbl_a = labeled_box(r"\mathrm{Source}", color=BLUE, scale=SCALE_LABEL)
        box_a.shift(-3.5, 0.0); lbl_a.move_to(-3.5, 0.0)

        box_b, lbl_b = labeled_box(r"\mathrm{Target}", color=PRIMARY, scale=SCALE_LABEL)
        box_b.shift(3.5, 0.0); lbl_b.move_to(3.5, 0.0)

        self.add(box_a, lbl_a, box_b, lbl_b)
        self.play(FadeIn(box_a, run_time=0.5), FadeIn(lbl_a, run_time=0.5),
                  FadeIn(box_b, run_time=0.5), FadeIn(lbl_b, run_time=0.5))

        # arrow_between: anchors at bbox edges, no hand-picking start/end
        arr = arrow_between(box_a, box_b, buff=0.15, color=GREY)
        self.add(arr)
        self.play(FadeIn(arr, run_time=0.5))

        # next_to: place a label above box_a relative to its bbox
        note = MathTex(r"\text{next\_to}", color=GREY, scale=SCALE_ANNOT)
        next_to(note, box_a, direction="UP", buff=0.4)
        self.add(note)
        self.play(FadeIn(note, run_time=0.4))

        bottom_lbl = MathTex(r"\text{ZONE\_BOTTOM}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(bottom_lbl, ZONE_BOTTOM)
        self.add(bottom_lbl)
        self.play(FadeIn(bottom_lbl, run_time=0.4))

        self.wait(2.5)
