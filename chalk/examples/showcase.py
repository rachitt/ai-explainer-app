from chalk import Scene, Circle, Square, Transform, MathTex


class Showcase(Scene):
    def construct(self) -> None:
        # Measure and stack from top down with explicit gaps
        rule = MathTex(r"(x^n)' = n\, x^{n-1}", color="#FFD700", scale=0.85)
        rule.move_to(0, 2.8)   # rule height ~0.8, spans [2.4, 3.2]
        self.add(rule)
        self.wait(1.2)

        # Three examples — compact inline notation, no fractions
        ex1 = MathTex(r"(x^2)' = 2x", color="#7EC8E3", scale=0.75)
        ex1.move_to(0, 1.2)
        ex2 = MathTex(r"(x^3)' = 3x^2", color="#7EC8E3", scale=0.75)
        ex2.move_to(0, 0.1)
        ex3 = MathTex(r"(x^4)' = 4x^3", color="#7EC8E3", scale=0.75)
        ex3.move_to(0, -1.0)

        for eq in (ex1, ex2, ex3):
            self.add(eq)
            self.wait(0.5)

        self.wait(0.8)

        # Shape morph at bottom
        c = Circle(radius=1.1, color="#E74C3C", fill_color="#E74C3C", fill_opacity=0.25, stroke_width=5.0)
        s = Square(side=2.2, color="#2ECC71", fill_color="#2ECC71", fill_opacity=0.25, stroke_width=5.0)
        c.shift(0, -2.9)
        s.shift(0, -2.9)
        self.add(c)
        self.wait(0.3)
        self.play(Transform(c, s), run_time=2.0)
        self.wait(0.8)
