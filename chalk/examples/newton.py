"""Newton's Second Law — beginner explainer.

Palette follows the color-and-typography skill:
  PRIMARY  #E8EAED  main text
  YELLOW   #FFD54F  result / punchline
  BLUE     #4FC3F7  variable / moving thing
  RED_FILL #EF5350  fills/strokes only (fails text contrast — never on labels)
  GREY     #9AA0A6  annotations / secondary labels

Zones (scene-composition skill, safe area y ∈ [-3.5, 3.5]):
  TOP     y ∈ [2.0, 3.5]   — the law + derived form
  CENTER  y ∈ [-2.0, 2.0]  — mass labels + circles
  BOTTOM  y ∈ [-3.5, -2.0] — acceleration payoff
"""
from chalk import Scene, Circle, Transform, MathTex

PRIMARY  = "#E8EAED"
YELLOW   = "#FFD54F"
BLUE     = "#4FC3F7"
RED_FILL = "#EF5350"
GREY     = "#9AA0A6"


class NewtonsSecondLaw(Scene):
    def construct(self) -> None:
        # ── TOP zone: introduce the law ───────────────────────────
        # Display math: scale ≈ 1.0; yellow = punchline/result
        law = MathTex(r"F = ma", color=YELLOW, scale=1.0)
        law.move_to(0, 2.75)
        self.add(law)
        self.wait(1.2)

        # Body math: scale ≈ 0.75; primary = derived insight
        derived = MathTex(r"a = F / m", color=PRIMARY, scale=0.75)
        derived.move_to(0, 1.85)
        self.add(derived)
        self.wait(1.5)

        # ── CENTER zone: same force, two masses ──────────────────
        # Labels: scale 0.55; BLUE for the variable (blue ball),
        # PRIMARY for the heavy ball (can't use RED_FILL on text)
        lbl_light = MathTex(r"m = 1\,\mathrm{kg}", color=BLUE, scale=0.55)
        lbl_light.move_to(-5.2, 1.2)

        lbl_heavy = MathTex(r"m = 9\,\mathrm{kg}", color=PRIMARY, scale=0.55)
        lbl_heavy.move_to(-5.2, -0.35)

        self.add(lbl_light, lbl_heavy)
        self.wait(0.5)

        # Circles at starting x = -5.2
        # Blue: small (light mass), accent_blue fill
        # Red:  large (heavy mass), accent_red fill — fill only, no text
        light = Circle(radius=0.3, color=BLUE, fill_color=BLUE,
                       fill_opacity=0.85, stroke_width=2.5)
        light.shift(-5.2, 0.55)

        heavy = Circle(radius=0.72, color=RED_FILL, fill_color=RED_FILL,
                       fill_opacity=0.85, stroke_width=2.5)
        heavy.shift(-5.2, -1.3)

        self.add(light, heavy)
        self.wait(0.8)

        # Same F, so a ∝ 1/m.  Light (m=1) moves 9× farther than heavy (m=9).
        light_end = Circle(radius=0.3, color=BLUE, fill_color=BLUE,
                           fill_opacity=0.85, stroke_width=2.5)
        light_end.shift(4.8, 0.55)

        heavy_end = Circle(radius=0.72, color=RED_FILL, fill_color=RED_FILL,
                           fill_opacity=0.85, stroke_width=2.5)
        heavy_end.shift(-4.2, -1.3)   # moves only 1 unit

        self.play(
            Transform(light, light_end),
            Transform(heavy, heavy_end),
            run_time=3.0,
        )
        self.wait(0.6)

        # ── BOTTOM zone: payoff (y ∈ [-2.0, -3.5]) ───────────────
        # Both acceleration labels in YELLOW = result color
        # Positioned near each ball's final x; safely inside bottom zone
        acc_light = MathTex(r"a = 9\,\mathrm{m/s^2}", color=YELLOW, scale=0.55)
        acc_light.move_to(4.8, -2.2)

        acc_heavy = MathTex(r"a = 1\,\mathrm{m/s^2}", color=GREY, scale=0.55)
        acc_heavy.move_to(-4.2, -2.4)

        self.add(acc_light, acc_heavy)
        self.wait(2.5)
