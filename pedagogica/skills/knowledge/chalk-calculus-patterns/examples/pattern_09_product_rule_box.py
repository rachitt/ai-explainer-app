"""Pattern 09 — Product rule as a box.

Rectangle with sides u, v (area = uv). Extend to (u+du)(v+dv).
New area = old uv + v·du strip + u·dv strip + du·dv corner (→0).
"""
from chalk import (
    Scene, Rectangle, MathTex,
    FadeIn, FadeOut, Write,
    LaggedStart,
    PRIMARY, BLUE, GREEN, YELLOW, GREY,
    SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone, next_to,
)


class ProductRuleBox(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Product rule: } d(uv) = v\,du + u\,dv",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        # ── Main rectangle uv ─────────────────────────────────────
        self.section("main_rect")
        u, v = 3.0, 2.4
        du, dv = 0.8, 0.6

        main = Rectangle(width=u, height=v,
                         fill_color=BLUE, fill_opacity=0.3,
                         color=BLUE, stroke_width=2.5)
        main.shift(-du / 2, -dv / 2)  # offset so extended rect is centred

        u_lbl = MathTex(r"u", color=BLUE, scale=SCALE_LABEL)
        v_lbl = MathTex(r"v", color=BLUE, scale=SCALE_LABEL)
        u_lbl.move_to(0.0, -v / 2 - dv / 2 - 0.35)
        v_lbl.move_to(-u / 2 - du / 2 - 0.35, 0.0)

        self.add(main, u_lbl, v_lbl)
        self.play(FadeIn(main, run_time=0.6))
        self.play(FadeIn(u_lbl, run_time=0.3), FadeIn(v_lbl, run_time=0.3))
        self.wait(0.5)

        # ── v·du strip (right) ────────────────────────────────────
        self.section("v_du_strip")
        strip_vdu = Rectangle(
            width=du, height=v,
            fill_color=GREEN, fill_opacity=0.5,
            color=GREEN, stroke_width=2.0,
        )
        strip_vdu.shift(u / 2 + du / 2 - du / 2, -dv / 2)

        vdu_lbl = MathTex(r"v\,du", color=GREEN, scale=SCALE_LABEL)
        next_to(vdu_lbl, strip_vdu, direction="RIGHT", buff=0.2)

        self.add(strip_vdu, vdu_lbl)
        self.play(FadeIn(strip_vdu, run_time=0.5))
        self.play(FadeIn(vdu_lbl, run_time=0.3))

        # ── u·dv strip (top) ──────────────────────────────────────
        self.section("u_dv_strip")
        strip_udv = Rectangle(
            width=u, height=dv,
            fill_color=YELLOW, fill_opacity=0.5,
            color=YELLOW, stroke_width=2.0,
        )
        strip_udv.shift(-du / 2, v / 2 + dv / 2 - dv / 2)

        udv_lbl = MathTex(r"u\,dv", color=YELLOW, scale=SCALE_LABEL)
        next_to(udv_lbl, strip_udv, direction="UP", buff=0.2)

        self.add(strip_udv, udv_lbl)
        self.play(FadeIn(strip_udv, run_time=0.5))
        self.play(FadeIn(udv_lbl, run_time=0.3))

        # ── du·dv corner (negligible) ────────────────────────────
        self.section("corner")
        corner = Rectangle(
            width=du, height=dv,
            fill_color=GREY, fill_opacity=0.4,
            color=GREY, stroke_width=1.5,
        )
        corner.shift(u / 2 + du / 2 - du / 2, v / 2 + dv / 2 - dv / 2)

        corner_lbl = MathTex(r"du\,dv \to 0", color=GREY, scale=SCALE_ANNOT)
        next_to(corner_lbl, corner, direction="RIGHT", buff=0.15)

        self.add(corner, corner_lbl)
        self.play(FadeIn(corner, run_time=0.4))
        self.play(FadeIn(corner_lbl, run_time=0.3))
        self.wait(0.5)
        self.play(FadeOut(corner, run_time=0.6), FadeOut(corner_lbl, run_time=0.6))

        # ── Payoff formula ────────────────────────────────────────
        self.section("payoff")
        payoff = MathTex(r"d(uv) = v\,du + u\,dv",
                         color=PRIMARY, scale=SCALE_BODY)
        place_in_zone(payoff, ZONE_BOTTOM)
        self.add(payoff)
        self.play(Write(payoff, run_time=1.2))
        self.wait(2.5)
