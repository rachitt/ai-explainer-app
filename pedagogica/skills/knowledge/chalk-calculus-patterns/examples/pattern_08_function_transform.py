"""Pattern 08 — Function transformation (shift / scale).

y=x² → y=x²+2 (shift up) → y=(x-1)² (shift right) → y=2x² (stretch).
Transform on graph VMobject; TransformMatchingTex on label.
"""
from chalk import (
    Scene, Axes, plot_function, MathTex,
    FadeIn, Write, Transform, TransformMatchingTex,
    BLUE, YELLOW, PRIMARY, GREY,
    SCALE_LABEL, SCALE_ANNOT,
    ZONE_TOP, ZONE_BOTTOM,
    place_in_zone,
)


class FunctionTransform(Scene):
    def construct(self):
        self.section("title")
        lbl = MathTex(r"\text{Function transformations of } y = x^2",
                      color=GREY, scale=SCALE_ANNOT)
        place_in_zone(lbl, ZONE_TOP)
        self.add(lbl)
        self.play(FadeIn(lbl, run_time=0.5))

        self.section("setup")
        ax = Axes(x_range=(-3.0, 3.0), y_range=(-0.5, 9.5),
                  width=7.5, height=5.5, x_step=1.0, y_step=2.0, color=GREY)
        self.add(ax)
        self.play(FadeIn(ax, run_time=0.6))

        f0 = lambda x: x ** 2
        graph = plot_function(ax, f0, color=BLUE, stroke_width=3.0)
        graph_lbl = MathTex(r"y = x^2", color=BLUE, scale=SCALE_LABEL)
        place_in_zone(graph_lbl, ZONE_BOTTOM)

        self.add(graph, graph_lbl)
        self.play(FadeIn(graph, run_time=0.8))
        self.play(Write(graph_lbl, run_time=0.6))
        self.wait(0.5)

        # Vertical shift up: y = x² + 2
        self.section("shift_up")
        f1 = lambda x: x ** 2 + 2
        g1 = plot_function(ax, f1, color=BLUE, stroke_width=3.0)
        l1 = MathTex(r"y = x^2 + 2", color=YELLOW, scale=SCALE_LABEL)
        place_in_zone(l1, ZONE_BOTTOM)

        self.play(Transform(graph, g1, run_time=1.2))
        self.play(TransformMatchingTex(graph_lbl, l1, run_time=0.9))
        graph_lbl = l1
        self.wait(0.6)

        # Horizontal shift right: y = (x-1)²
        self.section("shift_right")
        f2 = lambda x: (x - 1) ** 2
        g2 = plot_function(ax, f2, color=BLUE, stroke_width=3.0)
        l2 = MathTex(r"y = (x-1)^2", color=YELLOW, scale=SCALE_LABEL)
        place_in_zone(l2, ZONE_BOTTOM)

        self.play(Transform(graph, g2, run_time=1.2))
        self.play(TransformMatchingTex(graph_lbl, l2, run_time=0.9))
        graph_lbl = l2
        self.wait(0.6)

        # Vertical stretch: y = 2x²
        self.section("stretch")
        f3 = lambda x: 2 * x ** 2
        g3 = plot_function(ax, f3, color=BLUE, stroke_width=3.0)
        l3 = MathTex(r"y = 2x^2", color=PRIMARY, scale=SCALE_LABEL)
        place_in_zone(l3, ZONE_BOTTOM)

        self.play(Transform(graph, g3, run_time=1.2))
        self.play(TransformMatchingTex(graph_lbl, l3, run_time=0.9))
        self.wait(2.5)
