"""Kirchhoff's Circuit Laws — 20-second explainer.

Beat 1 (title) → Beat 2 (KCL at a node) → Beat 3 (KVL around a loop) → Beat 4 (payoff).

Requires LaTeX (basictex + tlmgr packages listed in workflows/lessons.md).
"""
from chalk import (
    Scene, Circle, Line, Arrow, MathTex, Text, VGroup,
    FadeIn, Write,
    PRIMARY, YELLOW, BLUE, GREEN, GREY,
    SCALE_DISPLAY, SCALE_LABEL,
    next_to, labeled_box,
)


class KirchhoffLaws(Scene):
    def construct(self) -> None:
        self._beat_title()
        self._beat_kcl()
        self._beat_kvl()
        self._beat_payoff()

    # ── Beat 1: title ────────────────────────────────────────────
    def _beat_title(self) -> None:
        title = Text("Kirchhoff's Circuit Laws", color=PRIMARY, scale=1.3)
        subtitle = Text("Two rules that govern every circuit", color=GREY, scale=0.75)
        title.move_to(0.0, 0.6)
        next_to(subtitle, title, direction="DOWN", buff=0.55)
        self.add(title)
        self.play(Write(title, run_time=1.4, lag_ratio=0.18))
        self.add(subtitle)
        self.play(Write(subtitle, run_time=0.9, lag_ratio=0.1))
        self.wait(1.2)
        self.clear(run_time=0.4)

    # ── Beat 2: KCL ──────────────────────────────────────────────
    def _beat_kcl(self) -> None:
        header = Text("KCL  —  current in = current out", color=YELLOW, scale=0.78)
        header.move_to(0.0, 3.0)
        self.add(header)
        self.play(Write(header, run_time=0.9, lag_ratio=0.08))

        node = Circle(radius=0.18, color=PRIMARY).set_fill(PRIMARY, 1.0)
        node.shift(0.0, 0.5)

        wire_l = Line((-3.6, 0.5), (-0.18, 0.5), color=GREY, stroke_width=2.2)
        wire_t = Line((-2.0, 2.3), (-0.05, 0.65), color=GREY, stroke_width=2.2)
        wire_r = Line((0.18, 0.5), (3.6, 0.5), color=GREY, stroke_width=2.2)

        i1 = Arrow((-2.7, 0.5), (-1.7, 0.5), color=BLUE)
        i2 = Arrow((-1.45, 1.75), (-0.8, 1.2), color=BLUE)
        i3 = Arrow((1.7, 0.5), (2.7, 0.5), color=YELLOW)

        l_i1 = MathTex(r"I_1", color=BLUE, scale=SCALE_LABEL)
        l_i2 = MathTex(r"I_2", color=BLUE, scale=SCALE_LABEL)
        l_i3 = MathTex(r"I_3", color=YELLOW, scale=SCALE_LABEL)
        next_to(l_i1, i1, direction="DOWN", buff=0.22)
        next_to(l_i2, i2, direction="LEFT", buff=0.22)
        next_to(l_i3, i3, direction="DOWN", buff=0.22)

        wires = VGroup(wire_l, wire_t, wire_r)
        arrows = VGroup(i1, i2, i3)
        labels = VGroup(l_i1, l_i2, l_i3)

        self.add(wires, node)
        self.play(FadeIn(wires, run_time=0.6), FadeIn(node, run_time=0.6))
        self.add(arrows, labels)
        self.play(Write(arrows, run_time=0.9, lag_ratio=0.5),
                  Write(labels, run_time=0.9, lag_ratio=0.5))

        eq = MathTex(r"I_1 + I_2 \;=\; I_3", color=PRIMARY, scale=SCALE_DISPLAY)
        eq.move_to(0.0, -2.6)
        self.add(eq)
        self.play(Write(eq, run_time=1.1, lag_ratio=0.22))
        self.wait(1.6)
        self.clear(run_time=0.4)

    # ── Beat 3: KVL ──────────────────────────────────────────────
    def _beat_kvl(self) -> None:
        header = Text("KVL  —  voltages around a loop sum to zero",
                      color=YELLOW, scale=0.7)
        header.move_to(0.0, 3.2)
        self.add(header)
        self.play(Write(header, run_time=1.0, lag_ratio=0.07))

        loop_w, loop_h = 5.0, 2.2
        cy = 0.4  # lift the loop slightly so it sits in center zone

        top    = Line((-loop_w / 2,  loop_h / 2 + cy),
                      ( loop_w / 2,  loop_h / 2 + cy), color=GREY, stroke_width=2.2)
        bottom = Line((-loop_w / 2, -loop_h / 2 + cy),
                      ( loop_w / 2, -loop_h / 2 + cy), color=GREY, stroke_width=2.2)
        left   = Line((-loop_w / 2,  loop_h / 2 + cy),
                      (-loop_w / 2, -loop_h / 2 + cy), color=GREY, stroke_width=2.2)
        right  = Line(( loop_w / 2,  loop_h / 2 + cy),
                      ( loop_w / 2, -loop_h / 2 + cy), color=GREY, stroke_width=2.2)

        batt, batt_lbl = labeled_box(
            r"V", color=GREEN, scale=SCALE_LABEL,
            fill_color=GREEN, fill_opacity=0.18,
        )
        batt.shift(-loop_w / 2, cy);  batt_lbl.move_to(-loop_w / 2, cy)

        r1, r1_lbl = labeled_box(
            r"R_1", color=BLUE, scale=SCALE_LABEL,
            fill_color=BLUE, fill_opacity=0.18,
        )
        r1.shift(0.0, loop_h / 2 + cy);  r1_lbl.move_to(0.0, loop_h / 2 + cy)

        r2, r2_lbl = labeled_box(
            r"R_2", color=BLUE, scale=SCALE_LABEL,
            fill_color=BLUE, fill_opacity=0.18,
        )
        r2.shift(loop_w / 2, cy);  r2_lbl.move_to(loop_w / 2, cy)

        i_arrow = Arrow((-0.9, loop_h / 2 + cy + 0.6),
                        ( 0.9, loop_h / 2 + cy + 0.6),
                        color=YELLOW)
        i_lbl = MathTex(r"I", color=YELLOW, scale=SCALE_LABEL)
        next_to(i_lbl, i_arrow, direction="UP", buff=0.2)

        wires = VGroup(top, bottom, left, right)
        comps = VGroup(batt, batt_lbl, r1, r1_lbl, r2, r2_lbl)

        self.add(wires)
        self.play(FadeIn(wires, run_time=0.6))
        self.add(comps)
        self.play(FadeIn(comps, run_time=0.7))
        self.add(i_arrow, i_lbl)
        self.play(FadeIn(i_arrow, run_time=0.4), FadeIn(i_lbl, run_time=0.4))

        eq = MathTex(r"V \;=\; I\,R_1 + I\,R_2",
                     color=PRIMARY, scale=SCALE_DISPLAY)
        eq.move_to(0.0, -2.7)
        self.add(eq)
        self.play(Write(eq, run_time=1.2, lag_ratio=0.22))
        self.wait(1.8)
        self.clear(run_time=0.4)

    # ── Beat 4: payoff ───────────────────────────────────────────
    def _beat_payoff(self) -> None:
        a = Text("Charge in = charge out", color=PRIMARY, scale=0.85)
        b = Text("Voltage around a loop = 0", color=YELLOW, scale=0.85)
        a.move_to(0.0, 0.7)
        next_to(b, a, direction="DOWN", buff=0.6)
        self.add(a)
        self.play(Write(a, run_time=1.1, lag_ratio=0.12))
        self.add(b)
        self.play(Write(b, run_time=1.1, lag_ratio=0.12))
        self.wait(2.3)
