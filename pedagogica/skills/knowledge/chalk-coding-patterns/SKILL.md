---
name: chalk-coding-patterns
description: Helper-first patterns for chalk coding scenes. Use when generating code tracing, recursion, call-stack, execution-cursor, tree-search, or algorithm walkthrough animations.
---

# Chalk Coding Patterns

## Rule

Reach for `CodeBlock`, `CallStack`, `Tree`, and `ExecutionCursor`. Never
hand-position monospace text, line arrows, stack boxes, or tree nodes when the
coding kit can express the scene.

## Component Palette

| Component | Semantic color | Typical use |
| --- | --- | --- |
| source | `PRIMARY` | code text |
| cursor | `YELLOW` | current execution line |
| highlight | `YELLOW` | active line or search path |

## Code Cursor Template

```python
from chalk import Scene, FadeIn, ShiftAnim, PRIMARY, YELLOW
from chalk.coding import CodeBlock, ExecutionCursor


class CodeTrace(Scene):
    def construct(self):
        code = CodeBlock("x = 1\ny = x + 2\nreturn y", color=PRIMARY)
        code.move_to(0.0, 0.0)
        cursor = ExecutionCursor(color=YELLOW)
        cursor.move_to_line(code, 0)
        code.highlight_line(0)
        self.add(code, cursor)
        self.play(FadeIn(code), FadeIn(cursor))
        self.play(ShiftAnim(cursor, dx=0.0, dy=code.line_y(1) - code.line_y(0)))
        code.unhighlight().highlight_line(1)
```

Use `code.line_y(idx)` or `cursor.move_to_line(code, idx)`. Do not hard-code
line y-coordinates.

## Call Stack Template

```python
from chalk import Scene, FadeIn, FadeOut, LaggedStart
from chalk.coding import CallStack


class StackTrace(Scene):
    def construct(self):
        stack = CallStack(x=0.0, y=1.2)
        for label in ["factorial(3)", "factorial(2)", "factorial(1)"]:
            stack.push(label)
        frames = list(reversed(stack.frames))
        self.add(*frames)
        self.play(LaggedStart(*[FadeIn(frame) for frame in frames], lag_ratio=0.4))
        for frame in list(stack.frames):
            self.play(FadeOut(frame))
            self.remove(frame)
            stack.pop()
```

Use `.top_frame` when an arrow needs to anchor to the active call; it exposes
`.center` and `.edge_toward(...)`.

## Binary Search Tree Template

```python
from chalk import Scene, FadeIn, PRIMARY, YELLOW
from chalk.coding import Tree


class BinarySearch(Scene):
    def construct(self):
        tree = Tree(
            nodes=[("8", (0, 2)), ("3", (-2, 0.5)), ("10", (2, 0.5)), ("6", (-1, -1))],
            edges=[(0, 1), (0, 2), (1, 3)],
            color=PRIMARY,
        )
        tree.highlight_path([0, 1, 3], color=YELLOW)
        self.add(tree)
        self.play(FadeIn(tree))
```

## Common Mistakes

- Using `MathTex` for code. Use `CodeBlock`; code is text, not math.
- Hard-coding line positions. Use `code.line_y(idx)` or `cursor.move_to_line`.
- Drawing stack frames as raw rectangles. Use `CallStack.push()` / `.pop()`.
- Building binary-search nodes by hand. Use `Tree` so nodes and edges share the
  graph kit's fitted-circle pattern.
