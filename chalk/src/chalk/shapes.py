"""Concrete VMobject shapes: Circle, Square, Dot, Polygon, RegularPolygon, ArcBetweenPoints."""
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


def _polygon_points(vertices: list[np.ndarray]) -> np.ndarray:
    """Build closed polygon from vertices using cubic Bezier line segments."""
    n = len(vertices)
    pts = []
    for i in range(n):
        p0 = vertices[i]
        p1 = vertices[(i + 1) % n]
        d = p1 - p0
        pts.extend([p0, p0 + d / 3, p0 + 2 * d / 3, p1])
    return np.array(pts, dtype=float)


def _arc_segment(
    center: np.ndarray, radius: float, a_start: float, a_end: float
) -> list[np.ndarray]:
    """One cubic Bezier approximation of an arc from a_start to a_end (radians)."""
    da = a_end - a_start
    alpha_c = (4 / 3) * math.tan(da / 4)
    cos0, sin0 = math.cos(a_start), math.sin(a_start)
    cos1, sin1 = math.cos(a_end), math.sin(a_end)
    p0 = center + radius * np.array([cos0, sin0])
    p3 = center + radius * np.array([cos1, sin1])
    p1 = p0 + radius * alpha_c * np.array([-sin0, cos0])
    p2 = p3 - radius * alpha_c * np.array([-sin1, cos1])
    return [p0, p1, p2, p3]


def _arc_points(
    center: np.ndarray, radius: float, a_start: float, angle: float
) -> np.ndarray:
    """Build Bezier arc of total angle `angle` (can be negative) starting at a_start."""
    n_segs = max(1, math.ceil(abs(angle) / (math.pi / 2)))
    da = angle / n_segs
    pts = []
    for i in range(n_segs):
        seg = _arc_segment(center, radius, a_start + i * da, a_start + (i + 1) * da)
        if i == 0:
            pts.extend(seg)
        else:
            pts.extend(seg[1:])  # skip duplicate start point
    return np.array(pts, dtype=float)


class Dot(Circle):
    """Filled circular dot at a given world-space point."""

    def __init__(
        self,
        point: tuple[float, float] = (0.0, 0.0),
        radius: float = 0.08,
        color: str = "#E8EAED",
        fill_opacity: float = 1.0,
    ) -> None:
        super().__init__(
            radius=radius,
            color=color,
            fill_color=color,
            fill_opacity=fill_opacity,
            stroke_width=0.0,
        )
        self.shift(point[0], point[1])


class Polygon(VMobject):
    """Closed polygon through given vertices."""

    def __init__(
        self,
        *vertices: tuple[float, float],
        color: str = "#E8EAED",
        fill_color: str | None = None,
        fill_opacity: float = 0.0,
        stroke_width: float = 2.5,
    ) -> None:
        super().__init__(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=fill_color or "#000000",
            fill_opacity=fill_opacity,
        )
        verts = [np.array(v, dtype=float) for v in vertices]
        self.points = _polygon_points(verts)


class RegularPolygon(Polygon):
    """Regular n-gon centered at origin."""

    def __init__(
        self,
        n: int,
        radius: float = 1.0,
        start_angle: float = 0.0,
        **kwargs,
    ) -> None:
        vertices = [
            (radius * math.cos(start_angle + 2 * math.pi * i / n),
             radius * math.sin(start_angle + 2 * math.pi * i / n))
            for i in range(n)
        ]
        super().__init__(*vertices, **kwargs)
        self.n = n
        self.radius = radius


class ArcBetweenPoints(VMobject):
    """Circular arc from start to end subtending `angle` radians.

    Positive angle curves left (counterclockwise from start→end perspective).
    angle=0 ≈ straight line.
    """

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        angle: float = math.pi / 3,
        color: str = "#E8EAED",
        stroke_width: float = 2.0,
        fill_opacity: float = 0.0,
    ) -> None:
        super().__init__(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_opacity=fill_opacity,
        )
        p0 = np.array(start, dtype=float)
        p1 = np.array(end, dtype=float)
        if abs(angle) < 1e-6:
            # Degenerate: straight line
            d = p1 - p0
            self.points = np.array([p0, p0 + d / 3, p0 + 2 * d / 3, p1])
            return
        chord = p1 - p0
        chord_len = float(np.linalg.norm(chord))
        if chord_len < 1e-9:
            self.points = np.array([p0, p0, p0, p0])
            return
        radius = chord_len / (2 * math.sin(abs(angle) / 2))
        # Unit vector along chord and perpendicular
        u = chord / chord_len
        perp = np.array([-u[1], u[0]])
        # Distance from chord midpoint to center (signed by angle direction)
        mid = (p0 + p1) / 2
        dist_to_center = radius * math.cos(abs(angle) / 2)
        # positive angle → center on the left of start→end
        sign = 1.0 if angle > 0 else -1.0
        center = mid - sign * dist_to_center * perp
        a_start = math.atan2(float(p0[1] - center[1]), float(p0[0] - center[0]))
        # CW sweep (−angle) curves left for positive angle in y-up coordinates
        self.points = _arc_points(center, radius, a_start, -angle)


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
