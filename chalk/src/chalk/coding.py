"""chalk.coding — domain primitive kit for code-tracing scenes.

Pure compositions of C1 primitives. No new renderer features.

Exports: CodeBlock, CallStack, Tree, ExecutionCursor
"""
from __future__ import annotations

import re

import numpy as np

from chalk.connectable import rect_edge_toward
from chalk.layout import labeled_box
from chalk.style import PRIMARY, YELLOW, BLUE, GREY, SCALE_BODY, SCALE_LABEL
from chalk.text import Text
from chalk.vgroup import VGroup


class CodeBlock(VGroup):
    """Monospace multi-line code block rendered as a VGroup of Text mobs per line.

    One line = one VMobject, so highlight_line(idx) can recolor it.
    Rendered left-aligned. Tabs expanded to 4 spaces. No syntax highlighting initially
    (add later via lexer tokens); use plain text for now.
    """

    def __init__(
        self,
        source: str,
        language: str = "python",
        color: str = PRIMARY,
        scale: float = SCALE_BODY,
        line_spacing: float = 1.2,
    ) -> None:
        self.source = source.expandtabs(4)
        self.language = language
        self.color = color
        self.scale_value = scale
        self.line_spacing = line_spacing
        self._line_step = scale * line_spacing
        self._highlighted: set[int] = set()

        self.lines = [
            Text(line if line else " ", color=color, scale=scale, font="Monospace")
            for line in self.source.splitlines()
        ]
        if not self.lines:
            self.lines = [Text(" ", color=color, scale=scale, font="Monospace")]

        left_x = 0.0
        for idx, line in enumerate(self.lines):
            _move_to(line, 0.0, self.line_y(idx))
            xmin, _ymin, _xmax, _ymax = _bbox(line)
            line.shift(left_x - xmin, 0.0)

        super().__init__(*self.lines)

    def bbox(self) -> tuple[float, float, float, float]:
        return _bbox(self)

    def move_to(self, x: float, y: float) -> "CodeBlock":
        cx, cy = _center(self)
        self.shift(x - cx, y - cy)
        return self

    def line_y(self, idx: int) -> float:
        """Return the y-coordinate of line ``idx`` relative to the block top."""
        self._check_line_index(idx)
        return -idx * self._line_step

    def line_center(self, idx: int) -> tuple[float, float]:
        """Return the world-space center of line ``idx``."""
        self._check_line_index(idx)
        return _center(self.lines[idx])

    def highlight_line(self, idx: int, color: str = YELLOW) -> "CodeBlock":
        self._check_line_index(idx)
        _set_color(self.lines[idx], color)
        self._highlighted.add(idx)
        return self

    def unhighlight(self) -> "CodeBlock":
        for idx in self._highlighted:
            _set_color(self.lines[idx], self.color)
        self._highlighted.clear()
        return self

    @property
    def n_lines(self) -> int:
        return len(self.lines)

    def _check_line_index(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.lines):
            raise IndexError(f"line index out of range: {idx}")


class _StackFrame(VGroup):
    def __init__(self, label: str, color: str = PRIMARY) -> None:
        self.label = label
        box, lbl = labeled_box(
            _frame_tex(label),
            color=color,
            scale=SCALE_LABEL,
            min_width=2.4,
            min_height=0.65,
            fill_color=GREY,
            fill_opacity=0.12,
        )
        super().__init__(box, lbl)

    def bbox(self) -> tuple[float, float, float, float]:
        return _bbox(self)

    def move_to(self, x: float, y: float) -> "_StackFrame":
        cx, cy = _center(self)
        self.shift(x - cx, y - cy)
        return self

    @property
    def center(self) -> tuple[float, float]:
        return _center(self)

    def edge_toward(self, target: tuple[float, float]) -> tuple[float, float]:
        xmin, ymin, xmax, ymax = _bbox(self)
        cx, cy = self.center
        return rect_edge_toward(
            cx,
            cy,
            (xmax - xmin) / 2,
            (ymax - ymin) / 2,
            target,
        )


class CallStack(VGroup):
    """Vertical stack of labeled frames (top=current call, bottom=base).

    Each frame is a labeled_box with the function name + args.
    push(frame_label) adds to top; pop() removes top.
    Exposes .top_frame as a Connectable so arrows can anchor there.
    """

    def __init__(
        self,
        frames: list[str] | None = None,
        x: float = 0.0,
        y: float = 0.0,
    ) -> None:
        self.x = x
        self.y = y
        self.frames: list[_StackFrame] = []
        super().__init__()
        for label in reversed(frames or []):
            self.push(label)

    def push(self, label: str) -> "CallStack":
        self.frames.insert(0, _StackFrame(label))
        self._relayout()
        return self

    def pop(self) -> "CallStack":
        if self.frames:
            self.frames.pop(0)
            self._relayout()
        return self

    @property
    def top_frame(self) -> _StackFrame:
        if not self.frames:
            raise ValueError("CallStack has no frames")
        return self.frames[0]

    def bbox(self) -> tuple[float, float, float, float]:
        return _bbox(self)

    def move_to(self, x: float, y: float) -> "CallStack":
        cx, cy = _center(self)
        self.shift(x - cx, y - cy)
        self.x += x - cx
        self.y += y - cy
        return self

    def _relayout(self) -> None:
        gap = 0.18
        next_center_y = self.y
        prev_height = 0.0
        for idx, frame in enumerate(self.frames):
            xmin, ymin, xmax, ymax = frame.bbox()
            height = ymax - ymin
            if idx == 0:
                next_center_y = self.y
            else:
                next_center_y -= prev_height / 2 + gap + height / 2
            frame.move_to(self.x, next_center_y)
            prev_height = height
        self.submobjects = list(self.frames)


class Tree(VGroup):
    """Simple binary/n-ary tree with hand-placed positions.

    Accepts list of (label, position) and edges drawn between parent/child
    positions. Nodes are fitted Circle with MathTex label, same pattern as
    chalk.graph.Node.
    """

    def __init__(
        self,
        nodes: list[tuple[str, tuple[float, float]]],
        edges: list[tuple[int, int]],
        color: str = PRIMARY,
    ) -> None:
        from chalk.graph import Edge, Node

        self.nodes = [
            Node(label, position=position, color=color)
            for label, position in nodes
        ]
        self.edges = [
            Edge(self.nodes[parent], self.nodes[child], directed=False, color=GREY)
            for parent, child in edges
        ]
        self.highlights: list = []
        super().__init__(*self.edges, *self.nodes)

    def highlight_path(self, node_indices: list[int], color: str = YELLOW) -> "Tree":
        from chalk.shapes import Circle

        for idx in node_indices:
            node = self.nodes[idx]
            ring = Circle(
                radius=node.fitted_radius + 0.1,
                color=color,
                stroke_width=3.5,
            )
            ring.shift(float(node.position[0]), float(node.position[1]))
            self.highlights.append(ring)
        self.submobjects = [*self.edges, *self.nodes, *self.highlights]
        return self


class ExecutionCursor(VGroup):
    """Small arrow marker that points at a code line; used with CodeBlock.

    Call cursor.move_to_line(code_block, idx) to reposition.
    Shift animation handles animated movement between lines.
    """

    def __init__(self, color: str = YELLOW) -> None:
        from chalk.shapes import Arrow

        self.color = color
        self._arrow = Arrow(
            (-0.45, 0.0),
            (0.0, 0.0),
            color=color,
            stroke_width=3.0,
            head_length=0.18,
            head_width=0.16,
            shaft_width=0.05,
        )
        super().__init__(self._arrow)

    def move_to_line(self, code: CodeBlock, idx: int) -> None:
        code._check_line_index(idx)
        xmin, ymin, _xmax, ymax = _bbox(code.lines[idx])
        target = (xmin - 0.22, (ymin + ymax) / 2)
        cx, cy = _center(self)
        self.shift(target[0] - cx, target[1] - cy)


def _frame_tex(label: str) -> str:
    if label.startswith("\\"):
        return label
    escaped = re.sub(r"([_{}])", r"\\\1", label)
    escaped = escaped.replace(" ", r"\ ")
    return rf"\mathrm{{{escaped}}}"


def _leaves(mob) -> list:
    if isinstance(mob, VGroup):
        out = []
        for child in mob.submobjects:
            out.extend(_leaves(child))
        return out
    return [mob]


def _bbox(mob) -> tuple[float, float, float, float]:
    pts = [leaf.points for leaf in _leaves(mob) if len(leaf.points) > 0]
    if not pts:
        return (0.0, 0.0, 0.0, 0.0)
    all_pts = np.vstack(pts)
    return (
        float(all_pts[:, 0].min()),
        float(all_pts[:, 1].min()),
        float(all_pts[:, 0].max()),
        float(all_pts[:, 1].max()),
    )


def _center(mob) -> tuple[float, float]:
    xmin, ymin, xmax, ymax = _bbox(mob)
    return ((xmin + xmax) / 2, (ymin + ymax) / 2)


def _move_to(mob, x: float, y: float) -> None:
    cx, cy = _center(mob)
    mob.shift(x - cx, y - cy)


def _set_color(mob, color: str) -> None:
    for leaf in _leaves(mob):
        leaf.stroke_color = color
        leaf.fill_color = color
