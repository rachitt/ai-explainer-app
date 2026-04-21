"""Newton's Second Law — beginner explainer.

Layout (y units, camera 14.2 × 8, safe area y ∈ [-3.5, 3.5]):

    y = +3.1   F = ma          (title)
    y = +2.3   a = F/m         (derived, muted)
    ─────────────────────────
    y = +1.6   m = 1 kg        (blue label, travels with ball)
    y = +0.8   [blue ball]     (r=0.3)
    y = +0.5   ─── track ───
    y = -0.2                   (space for blue acc after motion)
    ─────────────────────────
    y = -0.9   m = 9 kg        (heavy label, travels with ball)
    y = -2.0   [red ball]      (r=0.75)
    y = -2.75  ─── track ───
    y = -3.15                  (space for red acc after motion)
"""
from chalk import (
    Scene, Circle, Line, MathTex,
    ShiftAnim, FadeIn,
)

PRIMARY  = "#E8EAED"
YELLOW   = "#FFD54F"
BLUE     = "#4FC3F7"
RED_FILL = "#EF5350"
GREY     = "#9AA0A6"
TRACK    = "#2A2F36"


class NewtonsSecondLaw(Scene):
    def construct(self) -> None:
        # ── TITLE (y ∈ [2.0, 3.5]) ─────────────────────────────
        law = MathTex(r"F = ma", color=YELLOW, scale=0.85)
        law.move_to(0, 3.1)
        self.add(law)
        self.play(FadeIn(law, run_time=0.7))
        self.wait(0.9)

        derived = MathTex(r"a = F / m", color=GREY, scale=0.45)
        derived.move_to(0, 2.3)
        self.add(derived)
        self.play(FadeIn(derived, run_time=0.5))
        self.wait(1.0)

        # ── BLUE TRACK + LIGHT BALL ──────────────────────────────
        track_light = Line((-6.3, 0.5), (6.3, 0.5), color=TRACK, stroke_width=1.5)
        light = Circle(radius=0.3, color=BLUE, fill_color=BLUE,
                       fill_opacity=0.9, stroke_width=2.5)
        light.shift(-5.0, 0.8)
        light_lbl = MathTex(r"m = 1\,\mathrm{kg}", color=BLUE, scale=0.5)
        light_lbl.move_to(-5.0, 1.6)

        # ── RED TRACK + HEAVY BALL ──────────────────────────────
        track_heavy = Line((-6.3, -2.75), (6.3, -2.75), color=TRACK, stroke_width=1.5)
        heavy = Circle(radius=0.75, color=RED_FILL, fill_color=RED_FILL,
                       fill_opacity=0.9, stroke_width=2.5)
        heavy.shift(-5.0, -2.0)
        heavy_lbl = MathTex(r"m = 9\,\mathrm{kg}", color=PRIMARY, scale=0.5)
        heavy_lbl.move_to(-5.0, -0.9)

        self.add(track_light, track_heavy, light, heavy, light_lbl, heavy_lbl)
        self.play(
            FadeIn(track_light, run_time=0.5),
            FadeIn(track_heavy, run_time=0.5),
            FadeIn(light, run_time=0.7),
            FadeIn(heavy, run_time=0.7),
            FadeIn(light_lbl, run_time=0.7),
            FadeIn(heavy_lbl, run_time=0.7),
            run_time=0.8,
        )
        self.wait(1.3)

        # ── MOTION: same F → a ∝ 1/m ────────────────────────────
        # Light (m=1) shifts 9 units; heavy (m=9) shifts 1 unit.
        # Each label rides along with its ball.
        self.play(
            ShiftAnim(light,     dx=9.0, dy=0.0, run_time=3.0),
            ShiftAnim(light_lbl, dx=9.0, dy=0.0, run_time=3.0),
            ShiftAnim(heavy,     dx=1.0, dy=0.0, run_time=3.0),
            ShiftAnim(heavy_lbl, dx=1.0, dy=0.0, run_time=3.0),
            run_time=3.0,
        )
        self.wait(0.7)

        # ── PAYOFF: accelerations under each track ──────────────
        # Blue ball ended at x=4.0 → acc sits below blue track at (4.0, -0.2)
        acc_light = MathTex(r"a = 9\,\mathrm{m/s^2}", color=YELLOW, scale=0.55)
        acc_light.move_to(4.0, -0.2)

        # Heavy ball ended at x=-4.0 → acc sits below red track at (-4.0, -3.15)
        acc_heavy = MathTex(r"a = 1\,\mathrm{m/s^2}", color=GREY, scale=0.5)
        acc_heavy.move_to(-4.0, -3.2)

        self.add(acc_light, acc_heavy)
        self.play(
            FadeIn(acc_light, run_time=0.6),
            FadeIn(acc_heavy, run_time=0.6),
            run_time=0.6,
        )
        self.wait(2.8)
