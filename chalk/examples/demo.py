from chalk import Scene, Circle, Square, Transform


class Demo(Scene):
    def construct(self) -> None:
        c = Circle(radius=1.0, color="#3498db")
        s = Square(side=2.0, color="#e74c3c")
        self.add(c)
        self.play(Transform(c, s), run_time=2)
        self.wait(0.5)
