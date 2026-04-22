"""Second chalk.physics demo -- projectile motion and apex free-body diagram.

Run: uv run python -m chalk.cli chalk/examples/physics_demo2.py ProjectileDemo
"""
from chalk import (
    Scene,
    ValueTracker,
    always_redraw,
    FadeIn,
    ChangeValue,
    MoveAlongPath,
    MathTex,
    ParametricFunction,
    Dot,
    PRIMARY,
    YELLOW,
    BLUE,
    GREY,
    TRACK,
    SCALE_BODY,
    ZONE_TOP,
    place_in_zone,
)
from chalk.physics import Mass, Vector, FreeBody


class ProjectileDemo(Scene):
    def construct(self):
        def arc_point(t: float) -> tuple[float, float]:
            x0 = -4.6
            y0 = -1.5
            vx = 7.8
            vy = 4.6
            gravity = 5.2
            return (x0 + vx * t, y0 + vy * t - gravity * t * t)

        # -- Beat 1: launch velocity -----------------------------------------
        mass = Mass((-4.1, -1.2), label="m", show_weight=False)
        velocity = Vector(mass, (-2.2, 0.7), label=r"v_0", color=YELLOW)
        title = MathTex(r"\mathrm{Initial\ velocity}", color=GREY, scale=SCALE_BODY)
        place_in_zone(title, ZONE_TOP)
        self.add(title, mass, velocity)
        self.play(
            FadeIn(title, run_time=0.5),
            FadeIn(mass, run_time=0.5),
            FadeIn(velocity, run_time=0.6),
        )
        self.wait(1.0)
        self.clear()

        # -- Beat 2: trajectory under gravity --------------------------------
        t_tracker = ValueTracker(0.05)
        full_path = ParametricFunction(
            arc_point,
            t_range=(0.0, 1.0, 0.02),
            color=TRACK,
            stroke_width=2.0,
        )
        live_curve = always_redraw(
            lambda: ParametricFunction(
                arc_point,
                t_range=(0.0, max(t_tracker.get_value(), 0.05), 0.02),
                color=BLUE,
                stroke_width=3.0,
            )
        )
        ball = Dot(point=arc_point(0.0), radius=0.13, color=BLUE)

        def weight_vector() -> Vector:
            xmin = float(ball.points[:, 0].min())
            ymin = float(ball.points[:, 1].min())
            xmax = float(ball.points[:, 0].max())
            ymax = float(ball.points[:, 1].max())
            center = ((xmin + xmax) / 2, (ymin + ymax) / 2)
            return Vector(center, (center[0], center[1] - 0.9), label=r"mg", color=YELLOW)

        weight = always_redraw(weight_vector)
        curve_label = MathTex(r"y(t)=v_{0y}t-\frac{1}{2}gt^2", color=PRIMARY, scale=SCALE_BODY)
        place_in_zone(curve_label, ZONE_TOP)
        self.add(curve_label, full_path, live_curve, ball, weight)
        self.play(
            FadeIn(curve_label, run_time=0.4),
            FadeIn(full_path, run_time=0.4),
            FadeIn(live_curve, run_time=0.4),
            FadeIn(ball, run_time=0.4),
            FadeIn(weight, run_time=0.4),
        )
        self.play(
            ChangeValue(t_tracker, 1.0, run_time=2.8),
            MoveAlongPath(ball, full_path, run_time=2.8),
            run_time=2.8,
        )
        self.wait(0.5)
        self.clear()

        # -- Beat 3: apex free-body diagram ----------------------------------
        fbd = FreeBody(label="m", forces=[(1.5, 270.0, r"g")])
        apex_note = MathTex(r"\mathrm{At\ the\ apex:\ gravity\ only}", color=GREY, scale=SCALE_BODY)
        place_in_zone(apex_note, ZONE_TOP)
        self.add(apex_note, fbd)
        self.play(FadeIn(apex_note, run_time=0.5), FadeIn(fbd, run_time=0.6))
        self.wait(2.0)
