"""Second chalk.circuits demo -- RC charging through a resistor.

Run: uv run chalk chalk/examples/circuits_demo2.py --scene RCChargingDemo -o out.mp4
"""
import math

from chalk.circuits import (
    Battery,
    Capacitor,
    CurrentFlow,
    Resistor,
    SeriesLoop,
    VoltageLabel,
    Wire,
)

from chalk import (
    BLUE,
    GREEN,
    GREY,
    PRIMARY,
    SCALE_BODY,
    SCALE_LABEL,
    TRACK,
    YELLOW,
    ZONE_BOTTOM,
    Axes,
    ChangeValue,
    FadeIn,
    MathTex,
    Scene,
    Write,
    next_to,
    place_in_zone,
    plot_function,
)


class RCChargingDemo(Scene):
    def construct(self):
        def rc_loop():
            r1 = Resistor((-1.8, 1.4), (0.5, 1.4), color=PRIMARY)
            c1 = Capacitor((2.1, 1.4), (3.5, 1.4), color=BLUE)
            batt = Battery((-4.2, -0.4), (-4.2, 0.4), polarity="right", color=GREEN)
            loop_group = SeriesLoop(
                [r1, c1, batt],
                width=8.4,
                height=2.8,
                wire_color=GREY,
            )
            wire = next(mob for mob in loop_group.submobjects if isinstance(mob, Wire))
            v_label = VoltageLabel(
                across=(tuple(batt.start), tuple(batt.end)),
                value=r"V_0",
                side="UP",
            )
            r_label = MathTex(r"R", color=PRIMARY, scale=SCALE_LABEL)
            next_to(r_label, r1, direction="UP", buff=0.25)
            c_label = MathTex(r"C", color=BLUE, scale=SCALE_LABEL)
            next_to(c_label, c1, direction="UP", buff=0.25)
            return loop_group, wire, v_label, r_label, c_label

        # -- Beat 1: RC loop --------------------------------------------------
        loop_group, _wire, v_label, r_label, c_label = rc_loop()
        self.add(loop_group, v_label, r_label, c_label)
        self.play(
            FadeIn(loop_group, run_time=0.5),
            FadeIn(v_label, run_time=0.4),
            FadeIn(r_label, run_time=0.4),
            FadeIn(c_label, run_time=0.4),
        )
        self.wait(1.0)
        self.clear()

        # -- Beat 2: charging current ----------------------------------------
        loop_group, wire, v_label, r_label, c_label = rc_loop()
        flow = CurrentFlow(wire, charge_count=14, color=YELLOW)
        charge_label = MathTex(r"i(t)\ \mathrm{charges}\ C", color=YELLOW, scale=SCALE_BODY)
        place_in_zone(charge_label, ZONE_BOTTOM)
        self.add(loop_group, v_label, r_label, c_label, flow, charge_label)
        self.play(
            FadeIn(loop_group, run_time=0.4),
            FadeIn(v_label, run_time=0.4),
            FadeIn(r_label, run_time=0.4),
            FadeIn(c_label, run_time=0.4),
            FadeIn(flow, run_time=0.3),
            FadeIn(charge_label, run_time=0.4),
        )
        self.play(ChangeValue(flow.phase, 1.0, run_time=2.5))
        self.wait(0.4)
        self.clear()

        # -- Beat 3: capacitor voltage curve ---------------------------------
        axes = Axes(
            x_range=(0.0, 5.0),
            y_range=(0.0, 1.2),
            width=6.6,
            height=3.2,
            x_step=1.0,
            y_step=0.4,
            color=TRACK,
        )
        curve = plot_function(
            axes,
            lambda t: 1.0 - math.exp(-t),
            x_start=0.0,
            x_end=5.0,
            color=BLUE,
            stroke_width=3.0,
        )
        curve.closed = False
        v_axis = MathTex(r"V_C", color=GREY, scale=SCALE_LABEL)
        next_to(v_axis, axes, direction="LEFT", buff=0.3)
        t_axis = MathTex(r"t", color=GREY, scale=SCALE_LABEL)
        next_to(t_axis, axes, direction="DOWN", buff=0.3)
        equation = MathTex(r"V_C(t)=V_0(1-e^{-t/RC})", color=PRIMARY, scale=SCALE_BODY)
        next_to(equation, axes, direction="DOWN", buff=0.7)
        self.add(axes, v_axis, t_axis, curve, equation)
        self.play(
            FadeIn(axes, run_time=0.5),
            FadeIn(v_axis, run_time=0.4),
            FadeIn(t_axis, run_time=0.4),
        )
        self.play(Write(curve, run_time=1.2))
        self.play(FadeIn(equation, run_time=0.5))
        self.wait(2.0)
