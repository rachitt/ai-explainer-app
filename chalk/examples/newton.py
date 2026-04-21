from chalk import Scene, Circle, Transform, MathTex


class NewtonsSecondLaw(Scene):
    def construct(self) -> None:
        # ── Act 1: the law ──────────────────────────────────────
        law = MathTex(r"F = ma", color="#FFD700", scale=1.2)
        law.move_to(0, 3.2)
        self.add(law)
        self.wait(1.2)

        derived = MathTex(r"a = F / m", color="#CCCCCC", scale=0.8)
        derived.move_to(0, 2.3)
        self.add(derived)
        self.wait(1.5)

        # ── Act 2: same force, two masses ───────────────────────
        lbl1 = MathTex(r"m = 1\,\mathrm{kg}", color="#5BB8F5", scale=0.6)
        lbl1.move_to(-5.5, 1.5)

        lbl2 = MathTex(r"m = 9\,\mathrm{kg}", color="#F5625D", scale=0.6)
        lbl2.move_to(-5.5, -2.1)

        self.add(lbl1, lbl2)
        self.wait(0.5)

        blue = Circle(radius=0.3, color="#5BB8F5", fill_color="#5BB8F5",
                      fill_opacity=0.75, stroke_width=3.0)
        blue.shift(-5.5, 0.7)

        red = Circle(radius=0.75, color="#F5625D", fill_color="#F5625D",
                     fill_opacity=0.75, stroke_width=3.0)
        red.shift(-5.5, -0.9)

        self.add(blue, red)
        self.wait(0.8)

        # Same F → a ∝ 1/m.  blue (m=1) moves 9× farther than red (m=9).
        blue_end = Circle(radius=0.3, color="#5BB8F5", fill_color="#5BB8F5",
                          fill_opacity=0.75, stroke_width=3.0)
        blue_end.shift(3.5, 0.7)

        red_end = Circle(radius=0.75, color="#F5625D", fill_color="#F5625D",
                         fill_opacity=0.75, stroke_width=3.0)
        red_end.shift(-4.5, -0.9)

        self.play(
            Transform(blue, blue_end),
            Transform(red, red_end),
            run_time=3.0,
        )
        self.wait(0.6)

        # ── Act 3: reveal accelerations ──────────────────────────
        # F = 9 N  →  blue: a = 9/1 = 9 m/s²,  red: a = 9/9 = 1 m/s²
        acc1 = MathTex(r"a = 9\,\mathrm{m/s^2}", color="#5BB8F5", scale=0.6)
        acc1.move_to(3.5, 1.5)

        acc2 = MathTex(r"a = 1\,\mathrm{m/s^2}", color="#F5625D", scale=0.6)
        acc2.move_to(-4.5, -3.0)

        self.add(acc1, acc2)
        self.wait(2.5)
