"""chalk.coding demo -- code tracing, call stack, and tree walk.

Run: uv run chalk chalk/examples/coding_demo.py --scene CodingDemo -o out.mp4
"""
from chalk import (
    Scene,
    FadeIn,
    FadeOut,
    LaggedStart,
    ShiftAnim,
    PRIMARY,
    YELLOW,
)
from chalk.coding import CodeBlock, CallStack, Tree, ExecutionCursor


class CodingDemo(Scene):
    def construct(self):
        # -- Beat 1: execution cursor ----------------------------------------
        source = "\n".join([
            "def factorial(n):",
            "    if n <= 1:",
            "        return 1",
            "    return n * factorial(n - 1)",
            "",
            "factorial(3)",
        ])
        code = CodeBlock(source, color=PRIMARY)
        code.move_to(0.4, 0.1)
        cursor = ExecutionCursor(color=YELLOW)
        cursor.move_to_line(code, 1)
        code.highlight_line(1)

        self.add(code, cursor)
        self.play(FadeIn(code, run_time=0.7), FadeIn(cursor, run_time=0.4))
        self.wait(0.8)
        self.play(ShiftAnim(cursor, dx=0.0, dy=code.line_y(2) - code.line_y(1), run_time=0.7))
        code.unhighlight().highlight_line(2)
        self.wait(0.5)
        self.play(ShiftAnim(cursor, dx=0.0, dy=code.line_y(3) - code.line_y(2), run_time=0.7))
        code.unhighlight().highlight_line(3)
        self.wait(1.0)
        self.clear()

        # -- Beat 2: recursive call stack ------------------------------------
        stack = CallStack(x=0.0, y=1.2)
        for label in ["factorial(3)", "factorial(2)", "factorial(1)"]:
            stack.push(label)
        frames = list(reversed(stack.frames))
        self.add(*frames)
        self.play(
            LaggedStart(
                *[FadeIn(frame, run_time=0.5) for frame in frames],
                lag_ratio=0.45,
            )
        )
        self.wait(0.8)
        for frame in list(stack.frames):
            self.play(FadeOut(frame, run_time=0.35))
            self.remove(frame)
            stack.pop()
        self.wait(0.4)
        self.clear()

        # -- Beat 3: binary-search tree walk ---------------------------------
        tree = Tree(
            nodes=[
                ("8", (0.0, 2.0)),
                ("3", (-2.4, 0.5)),
                ("10", (2.4, 0.5)),
                ("1", (-3.4, -1.0)),
                ("6", (-1.4, -1.0)),
                ("14", (3.4, -1.0)),
                ("13", (2.4, -2.4)),
            ],
            edges=[(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (5, 6)],
            color=PRIMARY,
        )
        tree.highlight_path([0, 1, 4], color=YELLOW)
        self.add(tree)
        self.play(FadeIn(tree, run_time=0.8))
        self.wait(2.0)
