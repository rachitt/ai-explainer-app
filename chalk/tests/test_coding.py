"""Tests for chalk.coding: CodeBlock, CallStack, Tree, ExecutionCursor."""
from __future__ import annotations

from chalk.coding import CodeBlock, CallStack, Tree, ExecutionCursor
from chalk.style import PRIMARY, YELLOW


def _leaf_colors(mob) -> set[str]:
    if hasattr(mob, "submobjects"):
        colors: set[str] = set()
        for child in mob.submobjects:
            colors.update(_leaf_colors(child))
        return colors
    return {mob.fill_color}


def _center(mob) -> tuple[float, float]:
    xmin, ymin, xmax, ymax = mob.bbox()
    return ((xmin + xmax) / 2, (ymin + ymax) / 2)


def test_codeblock_n_lines():
    code = CodeBlock("def f():\n    return 1\nprint(f())")
    assert code.n_lines == 3


def test_codeblock_highlight_line():
    code = CodeBlock("a = 1\nb = 2\nc = a + b")
    code.highlight_line(1)

    assert _leaf_colors(code.lines[1]) == {YELLOW}
    assert _leaf_colors(code.lines[0]) == {PRIMARY}
    assert _leaf_colors(code.lines[2]) == {PRIMARY}


def test_callstack_push_pop():
    stack = CallStack()
    stack.push("factorial(3)").push("factorial(2)")
    assert len(stack.submobjects) == 2

    stack.pop()
    assert len(stack.submobjects) == 1


def test_callstack_top_connectable():
    stack = CallStack(["factorial(1)"])
    assert isinstance(stack.top_frame.center, tuple)
    assert isinstance(stack.top_frame.edge_toward((1.0, 0.0)), tuple)


def test_tree_construction():
    tree = Tree(
        nodes=[
            ("8", (0.0, 2.0)),
            ("3", (-2.0, 0.6)),
            ("10", (2.0, 0.6)),
            ("1", (-3.0, -1.0)),
            ("6", (-1.0, -1.0)),
            ("14", (3.0, -1.0)),
            ("13", (2.0, -2.4)),
        ],
        edges=[(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (5, 6)],
    )
    assert len(tree.nodes) == 7
    assert len(tree.edges) == 6
    assert len(tree.submobjects) == 13


def test_tree_highlight_path():
    tree = Tree(
        nodes=[("8", (0.0, 1.0)), ("3", (-1.0, 0.0)), ("6", (0.0, -1.0))],
        edges=[(0, 1), (1, 2)],
    )
    tree.highlight_path([0, 1, 2])

    assert len(tree.highlights) == 3
    assert all(ring.stroke_color == YELLOW for ring in tree.highlights)


def test_execution_cursor_move():
    code = CodeBlock("first\nsecond")
    cursor = ExecutionCursor()
    cursor.move_to_line(code, 0)
    before = _center(cursor)

    cursor.move_to_line(code, 1)
    after = _center(cursor)

    assert after != before
