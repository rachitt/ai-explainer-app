"""Concrete VMobject shapes: Circle and Square."""
from __future__ import annotations

import math
import numpy as np
from chalk.mobject import VMobject

# Cubic Bezier approximation constant for a quarter circle
_K = 0.5522847498


def _circle_points(radius: float) -> np.ndarray:
    """Build 64-point (16 cubic curves) closed circle approximation."""
    segments = 16
    pts = []
    angle_step = 2 * math.pi / segments
    for i in range(segments):
        a0 = i * angle_step
        a3 = (i + 1) * angle_step
        p0 = np.array([math.cos(a0), math.sin(a0)]) * radius
        p3 = np.array([math.cos(a3), math.sin(a3)]) * radius
        tangent0 = np.array([-math.sin(a0), math.cos(a0)]) * radius
        tangent3 = np.array([-math.sin(a3), math.cos(a3)]) * radius
        handle_len = _K * angle_step
        p1 = p0 + tangent0 * handle_len
        p2 = p3 - tangent3 * handle_len
        pts.extend([p0, p1, p2, p3])
    return np.array(pts, dtype=float)


def _square_points(side: float) -> np.ndarray:
    """Build 64-point (16 cubic curves) closed square approximation matching circle N."""
    return _rect_points(side, side)


def _rect_points(width: float, height: float) -> np.ndarray:
    """Build 64-point rectangle approximation (16 cubic line segments, 4 per side)."""
    w = width / 2
    h = height / 2
    corners = [
        np.array([-w, -h]),
        np.array([ w, -h]),
        np.array([ w,  h]),
        np.array([-w,  h]),
    ]
    segments = 16
    pts = []
    segs_per_side = segments // 4
    for side_idx in range(4):
        c0 = corners[side_idx]
        c1 = corners[(side_idx + 1) % 4]
        for seg in range(segs_per_side):
            t0 = seg / segs_per_side
            t1 = (seg + 1) / segs_per_side
            p0 = c0 + t0 * (c1 - c0)
            p3 = c0 + t1 * (c1 - c0)
            p1 = p0 + (p3 - p0) / 3
            p2 = p0 + 2 * (p3 - p0) / 3
            pts.extend([p0, p1, p2, p3])
    return np.array(pts, dtype=float)


class Circle(VMobject):
    def __init__(
        self,
        radius: float = 1.0,
        color: str = "#58C4DD",
        fill_color: str = "#000000",
        fill_opacity: float = 0.0,
        stroke_width: float = 3.0,
    ) -> None:
        super().__init__(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
        )
        self.radius = radius
        self.points = _circle_points(radius)


class Line(VMobject):
    """Straight line segment from (x0, y0) to (x1, y1)."""

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color: str = "#9AA0A6",
        stroke_width: float = 2.0,
        stroke_opacity: float = 1.0,
    ) -> None:
        super().__init__(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color="#000000",
            fill_opacity=0.0,
            stroke_opacity=stroke_opacity,
        )
        p0 = np.array(start, dtype=float)
        p1 = np.array(end, dtype=float)
        d = p1 - p0
        self.points = np.array([p0, p0 + d / 3, p0 + 2 * d / 3, p1])


class Square(VMobject):
    def __init__(
        self,
        side: float = 2.0,
        color: str = "#83C167",
        fill_color: str = "#000000",
        fill_opacity: float = 0.0,
        stroke_width: float = 3.0,
    ) -> None:
        super().__init__(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
        )
        self.side = side
        self.points = _square_points(side)


class Rectangle(VMobject):
    """Axis-aligned rectangle centered at origin."""

    def __init__(
        self,
        width: float = 2.0,
        height: float = 1.0,
        color: str = "#83C167",
        fill_color: str = "#000000",
        fill_opacity: float = 0.0,
        stroke_width: float = 3.0,
    ) -> None:
        super().__init__(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
        )
        self.width = width
        self.height = height
        self.points = _rect_points(width, height)


def _triangle_points(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Build a 12-point (3 cubic line segments) closed triangle from three vertices."""
    pts = []
    for p0, p1 in ((a, b), (b, c), (c, a)):
        d = p1 - p0
        pts.extend([p0, p0 + d / 3, p0 + 2 * d / 3, p1])
    return np.array(pts, dtype=float)


class Arrow(VMobject):
    """Straight arrow from start to end with a filled triangular head at end.

    Rendered as a single VMobject: one subpath for the shaft (stroke-only path
    that cairo treats as a skinny hairline region under evenodd), and one
    subpath for the triangular head.  We draw the head and shaft as separate
    elements by making the arrow itself a VGroup — see `make_arrow` below.
    For the common single-VMobject case we emit the outline of a filled arrow:
    a 7-vertex polygon forming shaft tail + head.
    """

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color: str = "#E8EAED",
        stroke_width: float = 2.0,
        head_length: float = 0.25,
        head_width: float = 0.2,
        shaft_width: float = 0.06,
        fill_opacity: float = 1.0,
    ) -> None:
        super().__init__(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=color,
            fill_opacity=fill_opacity,
            stroke_opacity=1.0,
        )
        p0 = np.array(start, dtype=float)
        p1 = np.array(end, dtype=float)
        direction = p1 - p0
        length = float(np.linalg.norm(direction))
        if length < 1e-9:
            self.points = _rect_points(0.0, 0.0)
            return
        u = direction / length
        perp = np.array([-u[1], u[0]])

        head_base = p1 - head_length * u
        sw = shaft_width / 2
        hw = head_width / 2

        # 7-vertex outline (counterclockwise):
        #   tail-bottom → tail-top → shaft-end-top → head-outer-top → tip
        #                                          → head-outer-bot → shaft-end-bot
        v = [
            p0 - sw * perp,              # tail bottom
            p0 + sw * perp,              # tail top
            head_base + sw * perp,       # shaft end top
            head_base + hw * perp,       # head flange top
            p1,                          # tip
            head_base - hw * perp,       # head flange bottom
            head_base - sw * perp,       # shaft end bottom
        ]
        pts = []
        for i in range(len(v)):
            a = v[i]
            b = v[(i + 1) % len(v)]
            d = b - a
            pts.extend([a, a + d / 3, a + 2 * d / 3, b])
        self.points = np.array(pts, dtype=float)
