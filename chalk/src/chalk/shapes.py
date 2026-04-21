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
    h = side / 2
    corners = [
        np.array([-h, -h]),
        np.array([h, -h]),
        np.array([h, h]),
        np.array([-h, h]),
    ]
    segments = 16
    pts = []
    # Distribute 16 segments evenly: 4 per side
    segs_per_side = segments // 4
    for side_idx in range(4):
        c0 = corners[side_idx]
        c1 = corners[(side_idx + 1) % 4]
        for seg in range(segs_per_side):
            t0 = seg / segs_per_side
            t1 = (seg + 1) / segs_per_side
            p0 = c0 + t0 * (c1 - c0)
            p3 = c0 + t1 * (c1 - c0)
            # Straight line: handles are 1/3 and 2/3 along the segment
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
