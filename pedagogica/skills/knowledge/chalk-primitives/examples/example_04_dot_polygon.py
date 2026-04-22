"""Dot, Polygon, RegularPolygon, ArcBetweenPoints.

Demonstrates: new shape primitives, angle convention for ArcBetweenPoints.
"""
import math
from chalk import (
    Scene, Dot, Polygon, RegularPolygon, ArcBetweenPoints,
    MathTex, FadeIn, LaggedStart,
    BLUE, GREEN, YELLOW, PRIMARY, GREY,
    SCALE_ANNOT,
    ZONE_TOP,
    place_in_zone,
)


class DotsAndPolygons(Scene):
    def construct(self):
        lbl = MathTex(r"\text{Dot, Polygon, RegularPolygon, ArcBetweenPoints}",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.4))

        # ArcBetweenPoints: positive angle → arc curves upward
        arc = ArcBetweenPoints((-3.0, 0.0), (3.0, 0.0),
                               angle=math.pi / 2, color=YELLOW, stroke_width=2.5)

        # Hexagon centred at origin
        hex6 = RegularPolygon(6, radius=1.0, color=BLUE, stroke_width=2.5)

        # Triangle
        tri = Polygon((-1.2, -0.8), (1.2, -0.8), (0.0, 1.0),
                      color=GREEN, stroke_width=2.5)

        # Dot at origin
        dot = Dot(point=(0.0, 0.5), radius=0.13, color=PRIMARY)

        self.add(arc, hex6, tri, dot)
        self.play(
            LaggedStart(
                FadeIn(arc,  run_time=0.7),
                FadeIn(hex6, run_time=0.7),
                FadeIn(tri,  run_time=0.7),
                FadeIn(dot,  run_time=0.4),
                lag_ratio=0.35,
            )
        )
        self.wait(2.0)
