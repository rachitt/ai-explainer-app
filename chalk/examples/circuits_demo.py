"""chalk.circuits demo — Resistor, Battery, Capacitor, Inductor, Switch,
Ground, Wire, CurrentFlow, VoltageLabel, KirchhoffDemo.

Run: uv run chalk chalk/examples/circuits_demo.py --scene CircuitsDemo -o out.mp4
"""
from chalk import (
    Scene, VGroup, ValueTracker,
    FadeIn, FadeOut, ChangeValue,
    PRIMARY, YELLOW, BLUE, GREEN, GREY,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL,
    next_to, MathTex,
)
from chalk.circuits import (
    Resistor, Battery, Capacitor, Inductor, Switch, Ground,
    Wire, CurrentFlow, VoltageLabel, KirchhoffDemo,
)


class CircuitsDemo(Scene):
    def construct(self):

        # ── Beat 1: component gallery ────────────────────────────────────────
        # Spread components across the frame with labels
        components = [
            ("Resistor",  Resistor((-5.5, 1.5), (-3.5, 1.5), color=PRIMARY)),
            ("Battery",   Battery((-1.8, 1.5), (0.2, 1.5), color=GREEN)),
            ("Capacitor", Capacitor((1.8, 1.5), (3.8, 1.5), color=BLUE)),
            ("Inductor",  Inductor((-5.5, -0.5), (-3.5, -0.5), color=PRIMARY)),
            ("Switch",    Switch((-1.8, -0.5), (0.2, -0.5), open=True, color=PRIMARY)),
            ("Ground",    Ground((2.8, -0.2), color=GREY)),
        ]

        for name, comp in components:
            lbl = MathTex(rf"\mathrm{{{name}}}", color=GREY, scale=0.5)
            pts = comp.bbox() if hasattr(comp, 'bbox') else None
            # Place label below component
            cx = (comp.submobjects[0].points[:, 0].mean()
                  if comp.submobjects else 0.0)
            cy = -1.5
            if name == "Ground":
                cx, cy = 2.8, -1.5
            lbl.move_to(cx, -1.0 if name in ("Inductor", "Switch", "Ground") else 0.9)
            self.add(comp, lbl)
            self.play(FadeIn(comp, run_time=0.3), FadeIn(lbl, run_time=0.3))

        self.wait(1.5)
        self.clear()

        # ── Beat 2: current flow along a wire loop ───────────────────────────
        batt = Battery((-4.0, -0.3), (-4.0, 0.3), color=GREEN)
        r1 = Resistor((-1.5, 1.5), (1.5, 1.5), color=PRIMARY)
        wire = Wire(
            (-4.0, 1.5), (4.0, 1.5), (4.0, -1.5), (-4.0, -1.5), (-4.0, 1.5),
            breaks=[r1, batt],
        )
        flow = CurrentFlow(wire, charge_count=12, color=YELLOW)
        lbl_r = MathTex(r"R_1", color=PRIMARY, scale=SCALE_LABEL)
        lbl_r.move_to(0.0, 2.0)
        vlbl = VoltageLabel(across=((-4.0, -0.3), (-4.0, 0.3)), value="V", side="UP")

        self.add(wire, batt, r1, lbl_r, vlbl)
        self.play(
            FadeIn(wire, run_time=0.5),
            FadeIn(batt, run_time=0.4),
            FadeIn(r1, run_time=0.4),
            FadeIn(lbl_r, run_time=0.4),
            FadeIn(vlbl, run_time=0.4),
        )
        self.add(flow)
        self.play(FadeIn(flow, run_time=0.3))
        self.play(ChangeValue(flow.phase, 1.0, run_time=2.5))
        self.wait(0.5)
        self.clear()

        # ── Beat 3: Kirchhoff demo assembled ────────────────────────────────
        demo = KirchhoffDemo()
        self.add(demo)
        self.play(FadeIn(demo, run_time=0.8))
        eq = MathTex(r"V = I\,R_1 + I\,R_2", color=PRIMARY, scale=0.9)
        eq.move_to(0.0, -3.2)
        self.add(eq)
        self.play(FadeIn(eq, run_time=0.6))
        self.wait(2.0)
        self.clear()
