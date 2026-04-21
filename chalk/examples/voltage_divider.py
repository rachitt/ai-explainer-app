"""The Voltage Divider — 45 s beginner explainer.

Splits an input voltage into a smaller output voltage by a fixed ratio of
resistors.  The formula V_out = V_in * R2 / (R1 + R2) is the single most
useful equation in analog circuit design.

Duration breakdown:
    0.0 –  4.0 s   Title
    4.0 – 14.0 s   Circuit diagram
   14.0 – 22.0 s   Formula reveal
   22.0 – 28.0 s   Labels gain numeric values
   28.0 – 40.0 s   Substitute + compute (step replaces formula)
   40.0 – 45.0 s   Final rest with result + caption
"""
from chalk import (
    Scene, Square, Circle, Line, MathTex,
    FadeIn, FadeOut,
    PRIMARY, YELLOW, BLUE, GREY, TRACK,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    next_to,
)


class VoltageDivider(Scene):
    def construct(self) -> None:
        # ── 0.0 – 4.0 s   Title ──────────────────────────────────
        title = MathTex(r"\mathrm{The\ Voltage\ Divider}",
                        color=YELLOW, scale=SCALE_DISPLAY)
        title.move_to(0, 3.1)
        self.add(title)
        self.play(FadeIn(title, run_time=0.8))
        self.wait(3.0)

        # ── 4.0 – 14.0 s   Circuit ───────────────────────────────
        # Vertical schematic: V_in → R1 → tap → R2 → GND at x = col_x.
        col_x   = -3.8
        v_top_y =  1.6
        r1_y    =  0.8
        tap_y   =  0.0
        r2_y    = -0.8
        v_bot_y = -1.6

        top_rail = Line((col_x - 0.8, v_top_y), (col_x + 0.8, v_top_y),
                        color=TRACK, stroke_width=2.0)
        wire_in    = Line((col_x, v_top_y), (col_x, r1_y + 0.3),
                          color=TRACK, stroke_width=2.0)
        wire_tap_a = Line((col_x, r1_y - 0.3), (col_x, tap_y),
                          color=TRACK, stroke_width=2.0)
        wire_tap_b = Line((col_x, tap_y), (col_x, r2_y + 0.3),
                          color=TRACK, stroke_width=2.0)
        wire_out   = Line((col_x, r2_y - 0.3), (col_x, v_bot_y),
                          color=TRACK, stroke_width=2.0)
        tap_lead   = Line((col_x, tap_y), (col_x + 2.2, tap_y),
                          color=TRACK, stroke_width=2.0)

        r1 = Square(side=0.6, color=BLUE, stroke_width=2.5)
        r1.shift(col_x, r1_y)
        r2 = Square(side=0.6, color=PRIMARY, stroke_width=2.5)
        r2.shift(col_x, r2_y)
        tap_dot = Circle(radius=0.08, color=YELLOW,
                         fill_color=YELLOW, fill_opacity=1.0, stroke_width=1.5)
        tap_dot.shift(col_x, tap_y)

        gnd_rail  = Line((col_x - 0.7, v_bot_y), (col_x + 0.7, v_bot_y),
                         color=TRACK, stroke_width=2.5)
        gnd_short = Line((col_x - 0.45, v_bot_y - 0.18), (col_x + 0.45, v_bot_y - 0.18),
                         color=TRACK, stroke_width=2.0)
        gnd_tiny  = Line((col_x - 0.22, v_bot_y - 0.36), (col_x + 0.22, v_bot_y - 0.36),
                         color=TRACK, stroke_width=1.5)

        vin_lbl  = MathTex(r"V_\mathrm{in}",  color=YELLOW,  scale=SCALE_LABEL)
        vin_lbl.move_to(col_x - 1.1, v_top_y)
        r1_lbl   = MathTex(r"R_1",            color=BLUE,    scale=SCALE_LABEL)
        next_to(r1_lbl, r1, direction="LEFT", buff=0.35)
        r2_lbl   = MathTex(r"R_2",            color=PRIMARY, scale=SCALE_LABEL)
        next_to(r2_lbl, r2, direction="LEFT", buff=0.35)
        vout_lbl = MathTex(r"V_\mathrm{out}", color=YELLOW,  scale=SCALE_LABEL)
        vout_lbl.move_to(col_x + 2.75, tap_y)

        circuit_wires = [
            top_rail, wire_in, wire_tap_a, wire_tap_b, wire_out,
            tap_lead, gnd_rail, gnd_short, gnd_tiny,
        ]
        circuit_parts = [r1, r2, tap_dot]
        circuit_labels = [vin_lbl, r1_lbl, r2_lbl, vout_lbl]

        for m in circuit_wires + circuit_parts + circuit_labels:
            self.add(m)

        self.play(
            *[FadeIn(w, run_time=0.5) for w in circuit_wires],
            *[FadeIn(p, run_time=0.7) for p in circuit_parts],
            *[FadeIn(l, run_time=0.7) for l in circuit_labels],
            run_time=0.9,
        )
        self.wait(9.0)

        # ── 14.0 – 22.0 s   Formula ──────────────────────────────
        formula = MathTex(
            r"V_\mathrm{out} = V_\mathrm{in}\cdot\dfrac{R_2}{R_1 + R_2}",
            color=PRIMARY, scale=SCALE_BODY,
        )
        formula.move_to(2.7, 1.1)
        self.add(formula)
        self.play(FadeIn(formula, run_time=0.9))
        self.wait(7.0)

        # ── 22.0 – 28.0 s   Give labels their values ─────────────
        vin_lbl_val = MathTex(r"V_\mathrm{in} = 12\,\mathrm{V}",
                              color=YELLOW,  scale=SCALE_LABEL)
        vin_lbl_val.move_to(col_x - 1.45, v_top_y)
        r1_lbl_val  = MathTex(r"R_1 = 3\,\Omega", color=BLUE,    scale=SCALE_LABEL)
        next_to(r1_lbl_val, r1, direction="LEFT", buff=0.35)
        r2_lbl_val  = MathTex(r"R_2 = 1\,\Omega", color=PRIMARY, scale=SCALE_LABEL)
        next_to(r2_lbl_val, r2, direction="LEFT", buff=0.35)

        self.add(vin_lbl_val, r1_lbl_val, r2_lbl_val)
        self.play(
            FadeOut(vin_lbl, run_time=0.4),
            FadeOut(r1_lbl,  run_time=0.4),
            FadeOut(r2_lbl,  run_time=0.4),
            FadeIn(vin_lbl_val, run_time=0.6),
            FadeIn(r1_lbl_val,  run_time=0.6),
            FadeIn(r2_lbl_val,  run_time=0.6),
            run_time=0.7,
        )
        self.wait(4.8)

        # ── 28.0 – 40.0 s   Substitute, step by step ─────────────
        # step1 replaces formula in the same spot
        step1 = MathTex(
            r"V_\mathrm{out} = 12 \cdot \dfrac{1}{3 + 1}",
            color=PRIMARY, scale=SCALE_BODY,
        )
        step1.move_to(2.7, 1.1)

        self.add(step1)
        self.play(
            FadeOut(formula, run_time=0.5),
            FadeIn(step1,    run_time=0.7),
            run_time=0.7,
        )
        self.wait(3.5)

        # step2 replaces step1 in the same spot, YELLOW for the final answer
        step2 = MathTex(
            r"V_\mathrm{out} = 3\,\mathrm{V}",
            color=YELLOW, scale=SCALE_DISPLAY,
        )
        step2.move_to(2.7, 1.1)

        self.add(step2)
        self.play(
            FadeOut(step1, run_time=0.5),
            FadeIn(step2,  run_time=0.8),
            run_time=0.8,
        )
        self.wait(6.5)

        # ── 40.0 – 45.0 s   Final caption ────────────────────────
        caption = MathTex(
            r"\mathrm{the\ ratio\ } R_2 / (R_1 + R_2) \mathrm{\ sets\ } V_\mathrm{out}",
            color=GREY, scale=SCALE_ANNOT,
        )
        caption.move_to(0, -3.0)
        self.add(caption)
        self.play(FadeIn(caption, run_time=0.7))
        self.wait(4.3)
