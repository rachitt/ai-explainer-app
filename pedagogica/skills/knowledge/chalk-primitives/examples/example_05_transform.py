"""Transform: morph Circle geometry into Rectangle.

Demonstrates: Transform, source stays on screen with target geometry.
"""
from chalk import (
    Scene, Circle, Rectangle, MathTex,
    FadeIn, Write, Transform,
    BLUE, GREEN, GREY,
    SCALE_ANNOT,
    ZONE_TOP, ZONE_CENTER,
    place_in_zone,
)


class TransformCircleToRect(Scene):
    def construct(self):
        lbl = MathTex(r"\text{Transform: Circle} \to \text{Rectangle}",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(Write(lbl, run_time=0.7))

        circle = Circle(radius=1.0, color=BLUE, stroke_width=3.0)
        place_in_zone(circle, ZONE_CENTER)
        self.add(circle)
        self.play(FadeIn(circle, run_time=0.5))
        self.wait(0.5)

        # Target: never added to scene; just defines the geometry to morph into
        rect = Rectangle(width=2.0, height=1.2, color=GREEN, stroke_width=3.0)
        place_in_zone(rect, ZONE_CENTER)

        self.play(Transform(circle, rect, run_time=1.2))
        # After: 'circle' is on screen holding rect's shape/color
        self.wait(2.0)
