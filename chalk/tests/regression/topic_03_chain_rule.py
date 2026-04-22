"""Pattern 06 — Chain rule composition (nested labeled boxes).

f(g(x)) = (x²+1)³. Show: x → g-box → g(x) → f-box → f(g(x)).
Then: derivative dx → g'(x)dx → f'(g(x))·g'(x)dx.
"""
from chalk import (
    Scene, MathTex,
    FadeIn, Write, TransformMatchingTex,
    AnimationGroup,
    PRIMARY, BLUE, GREEN, GREY,
    SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
    place_in_zone, next_to,
)
from chalk.layout import labeled_box, arrow_between


class ChainRuleBoxes(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Chain rule: } h(x) = (x^2+1)^3",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        # ── Composition diagram ──────────────────────────────────
        self.section("composition")
        box_g, lbl_g = labeled_box(r"g(x) = x^2+1", color=BLUE,
                                    scale=SCALE_LABEL, pad_x=0.4, pad_y=0.3)
        box_f, lbl_f = labeled_box(r"f(u) = u^3",   color=GREEN,
                                    scale=SCALE_LABEL, pad_x=0.4, pad_y=0.3)
        box_g.shift(-2.5, 0.3); lbl_g.move_to(-2.5, 0.3)
        box_f.shift( 2.5, 0.3); lbl_f.move_to( 2.5, 0.3)

        in_lbl  = MathTex(r"x",         color=PRIMARY, scale=SCALE_LABEL)
        mid_lbl = MathTex(r"g(x)",      color=BLUE,    scale=SCALE_LABEL)
        out_lbl = MathTex(r"f(g(x))",   color=GREEN,   scale=SCALE_LABEL)

        in_lbl.move_to( -5.5, 0.3)
        next_to(mid_lbl, box_g, direction="RIGHT", buff=0.5)
        next_to(out_lbl, box_f, direction="RIGHT", buff=0.5)

        arr1 = arrow_between(in_lbl,  box_g,   buff=0.1, color=GREY)
        arr2 = arrow_between(box_g,   box_f,   buff=0.1, color=GREY)
        arr3 = arrow_between(box_f,   out_lbl, buff=0.1, color=GREY)

        self.add(box_g, lbl_g, box_f, lbl_f, in_lbl, mid_lbl, out_lbl,
                 arr1, arr2, arr3)
        self.play(
            AnimationGroup(
                FadeIn(box_g, run_time=0.5), FadeIn(lbl_g, run_time=0.5),
                FadeIn(box_f, run_time=0.5), FadeIn(lbl_f, run_time=0.5),
                lag_ratio=0.3,
            )
        )
        self.play(
            AnimationGroup(
                FadeIn(in_lbl,  run_time=0.4),
                FadeIn(arr1,    run_time=0.4),
                FadeIn(mid_lbl, run_time=0.4),
                FadeIn(arr2,    run_time=0.4),
                FadeIn(out_lbl, run_time=0.4),
                FadeIn(arr3,    run_time=0.4),
                lag_ratio=0.25,
            )
        )
        self.wait(0.8)

        # ── Derivative step ──────────────────────────────────────
        self.section("derivative")
        deriv_lbl = MathTex(
            r"h'(x) = f'(g(x)) \cdot g'(x) = 3(x^2+1)^2 \cdot 2x",
            color=PRIMARY, scale=SCALE_LABEL,
        )
        place_in_zone(deriv_lbl, ZONE_BOTTOM)
        self.add(deriv_lbl)
        self.play(Write(deriv_lbl, run_time=1.5))
        self.wait(2.5)
