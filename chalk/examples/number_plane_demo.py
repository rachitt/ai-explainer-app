"""number_plane_demo: coordinate plane with a parabola plotted on it."""
from chalk import (
    Scene, MathTex, FadeIn,
    PRIMARY, YELLOW, BLUE, GREY, SCALE_BODY, SCALE_ANNOT,
    ZONE_TOP, place_in_zone,
    NumberPlane,
)
from chalk.shapes import Line
from chalk.vgroup import VGroup


class NumberPlaneDemo(Scene):
    def construct(self):
        title = MathTex(r"y = x^2", color=PRIMARY, scale=SCALE_BODY)
        place_in_zone(title, ZONE_TOP)
        self.add(title)
        self.play(FadeIn(title, run_time=0.6))

        plane = NumberPlane(
            x_range=(-5.0, 5.0, 1.0),
            y_range=(-3.0, 3.0, 1.0),
        )
        self.add(plane)
        self.play(FadeIn(plane, run_time=0.8))

        # Plot y = x^2 using short Line segments
        steps = 80
        x_lo, x_hi = -2.5, 2.5
        pts = []
        for i in range(steps + 1):
            t = i / steps
            x = x_lo + t * (x_hi - x_lo)
            y = x * x
            pts.append(plane.c2p(x, y))

        curve_segs = VGroup()
        for i in range(len(pts) - 1):
            seg = Line(pts[i], pts[i + 1], color=YELLOW, stroke_width=2.5)
            curve_segs.add(seg)

        self.add(curve_segs)
        self.play(FadeIn(curve_segs, run_time=1.2))
        self.wait(2.0)
