"""showcase.py — 70-second demo of all 10 chalk features.

Beat layout (sections):
  0:00 – title
  0:08 – feat1: ValueTracker + DecimalNumber
  0:18 – feat2: always_redraw + Rotate
  0:28 – feat3: MoveAlongPath
  0:38 – feat4: Shapes (Dot, Polygon, RegularPolygon, ArcBetweenPoints)
  0:48 – feat5: NumberLine + Brace
  0:58 – feat6: TransformMatchingTex + Circumscribe
  1:08 – feat7: AnimationGroup / LaggedStart / Succession + Flash
"""
import math

from chalk import (
    Scene, MathTex, Circle, Rectangle, Line,
    FadeIn, FadeOut, Write,
    ChangeValue, MoveAlongPath, Rotate,
    AnimationGroup, Succession, LaggedStart,
    Indicate, Flash, Circumscribe,
    TransformMatchingTex,
    ValueTracker, DecimalNumber, always_redraw,
    Dot, Polygon, RegularPolygon, ArcBetweenPoints,
    NumberLine,
    Brace, brace_label,
    PRIMARY, YELLOW, BLUE, GREEN, RED_FILL, GREY, TRACK,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
    place_in_zone, next_to,
)
from chalk.rate_funcs import linear
from chalk.vgroup import VGroup


class Showcase(Scene):
    def construct(self):

        # ── Beat 0: Title (0:00 – 0:08) ─────────────────────────────────────
        self.section("title")

        title = MathTex(r"\textbf{chalk} \text{ — 10 new features}", color=PRIMARY,
                        scale=SCALE_DISPLAY)
        place_in_zone(title, ZONE_CENTER)
        sub = MathTex(r"\text{C1 parity floor}", color=GREY, scale=SCALE_ANNOT)
        next_to(sub, title, direction="DOWN", buff=0.4)

        self.add(title, sub)
        self.play(Write(title, run_time=1.4), FadeIn(sub, run_time=0.9))
        self.wait(7.0)
        self.clear(run_time=0.5)

        # ── Beat 1: ValueTracker + DecimalNumber (0:08 – 0:18) ───────────────
        self.section("feat1_valuetracker")

        lbl1 = MathTex(r"\text{1. ValueTracker + DecimalNumber}", color=YELLOW,
                       scale=SCALE_BODY)
        place_in_zone(lbl1, ZONE_TOP)
        self.add(lbl1)
        self.play(FadeIn(lbl1, run_time=0.5))

        tracker = ValueTracker(0.0)
        counter = DecimalNumber(tracker, num_decimal_places=0,
                                color=PRIMARY, scale=SCALE_DISPLAY)
        place_in_zone(counter, ZONE_CENTER)
        self.add(counter)

        self.play(ChangeValue(tracker, 100.0, run_time=5.0, rate_func=linear))
        self.wait(2.5)
        self.clear(run_time=0.4)

        # ── Beat 2: always_redraw + Rotate (0:18 – 0:28) ────────────────────
        self.section("feat2_redraw_rotate")

        lbl2 = MathTex(r"\text{2. always\_redraw + Rotate}", color=YELLOW,
                       scale=SCALE_BODY)
        place_in_zone(lbl2, ZONE_TOP)
        self.add(lbl2)
        self.play(FadeIn(lbl2, run_time=0.5))

        t2 = ValueTracker(0.0)
        sq = Rectangle(width=2.0, height=2.0, color=BLUE, stroke_width=3.0)
        self.add(sq)
        self.play(FadeIn(sq, run_time=0.4))

        angle_disp = always_redraw(
            lambda: MathTex(
                rf"\theta = {t2.get_value():.0f}^\circ",
                color=GREY, scale=SCALE_LABEL,
            ).move_to(0.0, -2.6)
        )
        self.add(angle_disp)

        self.play(
            Rotate(sq, angle=2 * math.pi, about_point=(0.0, 0.0),
                   run_time=4.0, rate_func=linear),
            ChangeValue(t2, 360.0, run_time=4.0, rate_func=linear),
        )
        self.wait(2.0)
        self.clear(run_time=0.4)

        # ── Beat 3: MoveAlongPath (0:28 – 0:38) ─────────────────────────────
        self.section("feat3_movealongpath")

        lbl3 = MathTex(r"\text{3. MoveAlongPath}", color=YELLOW, scale=SCALE_BODY)
        place_in_zone(lbl3, ZONE_TOP)
        self.add(lbl3)
        self.play(FadeIn(lbl3, run_time=0.5))

        orbit_ring = Circle(radius=2.2, color=GREY, stroke_width=1.2)
        dot3 = Dot(point=(2.2, 0.0), radius=0.14, color=YELLOW)
        self.add(orbit_ring, dot3)
        self.play(FadeIn(orbit_ring, run_time=0.4), FadeIn(dot3, run_time=0.3))
        self.play(MoveAlongPath(dot3, orbit_ring, run_time=5.0, rate_func=linear))
        self.wait(1.5)
        self.clear(run_time=0.4)

        # ── Beat 4: Shapes (0:38 – 0:48) ────────────────────────────────────
        self.section("feat4_shapes")

        lbl4 = MathTex(
            r"\text{4. Dot, Polygon, RegularPolygon, ArcBetweenPoints}",
            color=YELLOW, scale=SCALE_ANNOT,
        )
        place_in_zone(lbl4, ZONE_TOP)
        self.add(lbl4)
        self.play(FadeIn(lbl4, run_time=0.5))

        hex6 = RegularPolygon(6, radius=1.1, color=BLUE, stroke_width=2.5)
        tri  = Polygon((-1.4, -0.8), (1.4, -0.8), (0.0, 1.2),
                       color=GREEN, stroke_width=2.5)
        arc4 = ArcBetweenPoints((-2.6, 0.0), (2.6, 0.0),
                                angle=math.pi / 2, color=YELLOW, stroke_width=2.5)
        dot4 = Dot(point=(0.0, 0.6), radius=0.13, color=PRIMARY)

        self.add(hex6, tri, arc4, dot4)
        self.play(
            LaggedStart(
                FadeIn(hex6, run_time=0.7),
                FadeIn(tri,  run_time=0.7),
                FadeIn(arc4, run_time=0.7),
                FadeIn(dot4, run_time=0.5),
                lag_ratio=0.4,
            )
        )
        self.wait(0.6)
        self.play(Indicate(hex6, scale_factor=1.2, color=BLUE, run_time=1.0))
        self.wait(3.0)
        self.clear(run_time=0.4)

        # ── Beat 5: NumberLine + Brace (0:48 – 0:58) ────────────────────────
        self.section("feat5_coord_brace")

        lbl5 = MathTex(r"\text{5. NumberLine + Brace}", color=YELLOW,
                       scale=SCALE_BODY)
        place_in_zone(lbl5, ZONE_TOP)
        self.add(lbl5)
        self.play(FadeIn(lbl5, run_time=0.4))

        nl = NumberLine(x_range=(-4.0, 4.0, 1.0), length=8.0,
                        include_numbers=True, color=GREY)
        self.add(nl)
        self.play(FadeIn(nl, run_time=0.6))

        seg_line = Line((0.0, 0.0), (4.0, 0.0), color=YELLOW, stroke_width=4.0)
        dot5a = Dot(point=(0.0, 0.0), radius=0.10, color=YELLOW)
        dot5b = Dot(point=(4.0, 0.0), radius=0.10, color=YELLOW)
        self.add(seg_line, dot5a, dot5b)
        self.play(FadeIn(seg_line, run_time=0.5),
                  FadeIn(dot5a, run_time=0.4), FadeIn(dot5b, run_time=0.4))

        brace5, blbl5 = brace_label(seg_line, r"\Delta x = 4",
                                     direction="UP", color=YELLOW, scale=SCALE_LABEL)
        self.add(brace5, blbl5)
        self.play(FadeIn(brace5, run_time=0.5), FadeIn(blbl5, run_time=0.5))
        self.wait(3.0)
        self.clear(run_time=0.4)

        # ── Beat 6: TransformMatchingTex + Circumscribe (0:58 – 1:08) ────────
        self.section("feat6_tex_morph")

        lbl6 = MathTex(r"\text{6. TransformMatchingTex + Circumscribe}",
                       color=YELLOW, scale=SCALE_ANNOT)
        place_in_zone(lbl6, ZONE_TOP)
        self.add(lbl6)
        self.play(FadeIn(lbl6, run_time=0.4))

        eq1 = MathTex(r"F = ma", color=PRIMARY, scale=SCALE_DISPLAY)
        place_in_zone(eq1, ZONE_CENTER)
        eq2 = MathTex(r"a = F/m", color=YELLOW, scale=SCALE_DISPLAY)
        place_in_zone(eq2, ZONE_CENTER)

        self.add(eq1)
        self.play(Write(eq1, run_time=1.0))
        self.wait(0.4)
        self.play(Circumscribe(eq1, shape="rect", color=BLUE, buff=0.2, run_time=0.8))
        self.wait(0.3)
        self.play(TransformMatchingTex(eq1, eq2, run_time=1.8))
        self.wait(4.5)
        self.clear(run_time=0.4)

        # ── Beat 7: AnimationGroup + Flash + Succession (1:08 – 1:18) ────────
        self.section("feat7_animation_group")

        lbl7 = MathTex(r"\text{7. AnimationGroup + Flash}", color=YELLOW,
                       scale=SCALE_BODY)
        place_in_zone(lbl7, ZONE_TOP)
        self.add(lbl7)
        self.play(FadeIn(lbl7, run_time=0.4))

        positions = [(-4.0, 0.0), (-1.5, 0.0), (1.5, 0.0), (4.0, 0.0)]
        colors    = [BLUE, GREEN, YELLOW, PRIMARY]
        shapes7   = [
            Circle(radius=0.55, color=colors[0], stroke_width=2.5),
            Rectangle(width=1.1, height=1.1, color=colors[1], stroke_width=2.5),
            RegularPolygon(5, radius=0.6, color=colors[2], stroke_width=2.5),
            Dot(point=(0.0, 0.0), radius=0.14, color=colors[3]),
        ]
        for s, (x, y) in zip(shapes7, positions):
            s.shift(x, y)
            self.add(s)

        self.play(
            AnimationGroup(*[FadeIn(s, run_time=0.7) for s in shapes7], lag_ratio=0.3)
        )
        self.wait(0.4)

        # Flash at each shape center in Succession
        flashes = [
            Flash(pos, color=YELLOW, num_lines=10, line_length=0.28, run_time=0.5)
            for pos in positions
        ]
        for f in flashes:
            for m in f.mobjects:
                self.add(m)

        self.play(Succession(*flashes))
        self.wait(2.0)
        self.clear(run_time=0.5)

        # ── Finale (1:18 – 1:22) ────────────────────────────────────────────
        self.section("finale")

        finale = MathTex(r"\text{chalk — C1 parity floor} \checkmark",
                         color=YELLOW, scale=SCALE_DISPLAY)
        place_in_zone(finale, ZONE_CENTER)
        self.add(finale)
        self.play(Write(finale, run_time=1.5))
        self.wait(5.0)
