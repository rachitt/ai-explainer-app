from chalk import Scene, MathTex


class DerivativeDemo(Scene):
    def construct(self) -> None:
        eq = MathTex(r"\frac{d}{dx} x^2 = 2x", color="#FFD700", scale=0.8)
        eq.shift(0, 1.0)
        self.add(eq)
        self.wait(2.0)
