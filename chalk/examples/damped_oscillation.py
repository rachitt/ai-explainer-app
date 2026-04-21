"""Damped Oscillation — 30 s beginner explainer.

Shows a mass on a spring with friction.  Displacement x(t) decays as a sine
wave under an exponential envelope: x(t) = A e^{-γt} cos(ω t).

Uses Axes + plot_function + Arrow + Rectangle.
"""
import math

from chalk import (
    Scene, Rectangle, Circle, Line, Arrow,
    Axes, plot_function, MathTex,
    FadeIn, FadeOut,
    PRIMARY, YELLOW, BLUE, GREY, TRACK, RED_FILL,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT,
    next_to,
)


class DampedOscillation(Scene):
    def construct(self) -> None:
        # ── 0 – 3 s   Title ───────────────────────────────────────
        title = MathTex(r"\mathrm{Damped\ Oscillation}",
                        color=YELLOW, scale=SCALE_DISPLAY)
        title.move_to(0, 3.1)
        self.add(title)
        self.play(FadeIn(title, run_time=0.8))
        self.wait(2.0)

        # ── 3 – 10 s   Axes + damped sine plot ───────────────────
        axes = Axes(
            x_range=(0, 10), y_range=(-1.2, 1.2),
            width=11.5, height=3.6,
            x_step=1.0, y_step=0.5,
            color=GREY, stroke_width=2.0,
        )
        axes.shift(0, -0.2)
        self.add(axes)
        self.play(
            *[FadeIn(sub, run_time=0.5) for sub in axes.submobjects],
            run_time=0.7,
        )

        x_lbl = MathTex(r"t", color=GREY, scale=SCALE_LABEL)
        x_lbl.move_to(5.9, -0.4)
        y_lbl = MathTex(r"x(t)", color=GREY, scale=SCALE_LABEL)
        y_lbl.move_to(-5.6, 1.4)
        self.add(x_lbl, y_lbl)
        self.play(FadeIn(x_lbl, run_time=0.4), FadeIn(y_lbl, run_time=0.4),
                  run_time=0.5)
        self.wait(0.5)

        # Two curves: envelope (+/- A*e^{-γt}) in RED_FILL, signal in BLUE
        gamma = 0.35
        omega = 2.2

        def env_plus(t):  return math.exp(-gamma * t)
        def env_minus(t): return -math.exp(-gamma * t)
        def signal(t):    return math.exp(-gamma * t) * math.cos(omega * t)

        env_a = plot_function(axes, env_plus,  resolution=100,
                              color=RED_FILL, stroke_width=1.8)
        env_b = plot_function(axes, env_minus, resolution=100,
                              color=RED_FILL, stroke_width=1.8)
        env_a.stroke_opacity = 0.55
        env_b.stroke_opacity = 0.55
        # shift to match axes (which are shifted by (0, -0.2))
        env_a.shift(0, -0.2)
        env_b.shift(0, -0.2)
        self.add(env_a, env_b)
        self.play(FadeIn(env_a, run_time=0.7), FadeIn(env_b, run_time=0.7),
                  run_time=0.8)
        self.wait(0.4)

        curve = plot_function(axes, signal, resolution=160,
                              color=BLUE, stroke_width=3.0)
        curve.shift(0, -0.2)
        self.add(curve)
        self.play(FadeIn(curve, run_time=1.2))
        self.wait(2.0)

        # ── 10 – 18 s   Equation ──────────────────────────────────
        eq = MathTex(r"x(t) = A\, e^{-\gamma t}\cos(\omega t)",
                     color=PRIMARY, scale=SCALE_BODY)
        eq.move_to(0, 2.25)
        self.add(eq)
        self.play(FadeIn(eq, run_time=0.9))
        self.wait(6.5)

        # ── 18 – 25 s   Point out the envelope with an arrow ─────
        # Arrow pointing from a caption to the RED envelope
        caption = MathTex(r"A\, e^{-\gamma t}",
                          color=RED_FILL, scale=SCALE_LABEL)
        caption.move_to(3.0, 1.7)
        # Anchor the arrow from the caption's bottom to a point on the envelope
        # envelope at t=4  →  world x = axes.to_point(4, 0)[0] = 4*11.5/10 - 5.75
        tx = axes.to_point(4.0, 0.0)[0]
        ty = axes.to_point(0.0, env_plus(4.0))[1] + (-0.2)  # +axes shift

        cx0, cy0, cx1, cy1 = caption.bbox()
        arr = Arrow(
            start=(cx0 + 0.1, cy0 - 0.1),
            end=(tx, ty + 0.1),
            color=RED_FILL, stroke_width=1.5,
            head_length=0.25, head_width=0.22, shaft_width=0.05,
        )
        self.add(caption, arr)
        self.play(FadeIn(caption, run_time=0.6),
                  FadeIn(arr,     run_time=0.6),
                  run_time=0.7)
        self.wait(5.5)

        # ── 25 – 30 s   Takeaway ─────────────────────────────────
        takeaway = MathTex(
            r"\mathrm{friction\ drains\ energy\ so\ amplitude\ decays}",
            color=GREY, scale=SCALE_ANNOT)
        takeaway.move_to(0, -3.0)
        self.add(takeaway)
        self.play(FadeIn(takeaway, run_time=0.7))
        self.wait(4.0)
