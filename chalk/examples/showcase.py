from chalk import Scene, Circle, Square, Transform, MathTex


class Showcase(Scene):
    def construct(self) -> None:
        # Title equation
        title = MathTex(r"\frac{d}{dx}\left[x^n\right] = nx^{n-1}", color="#FFD700", scale=0.9)
        title.shift(0, 3.0)
        self.add(title)
        self.wait(1.5)

        # Power rule instances stacked
        line1 = MathTex(r"x^2 \;\longrightarrow\; 2x", color="#7EC8E3", scale=0.7)
        line1.shift(0, 1.2)
        line2 = MathTex(r"x^3 \;\longrightarrow\; 3x^2", color="#7EC8E3", scale=0.7)
        line2.shift(0, 0.0)
        line3 = MathTex(r"x^4 \;\longrightarrow\; 4x^3", color="#7EC8E3", scale=0.7)
        line3.shift(0, -1.2)

        self.add(line1)
        self.wait(0.5)
        self.add(line2)
        self.wait(0.5)
        self.add(line3)
        self.wait(1.0)

        # Morph circle into square (visual punctuation)
        c = Circle(radius=1.2, color="#E74C3C", fill_color="#E74C3C", fill_opacity=0.3, stroke_width=4.0)
        s = Square(side=2.4, color="#2ECC71", fill_color="#2ECC71", fill_opacity=0.3, stroke_width=4.0)
        c.shift(0, -3.0)
        s.shift(0, -3.0)

        self.add(c)
        self.wait(0.3)
        self.play(Transform(c, s), run_time=2.0)
        self.wait(1.0)
