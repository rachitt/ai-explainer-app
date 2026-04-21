"""Axes: 2D coordinate system with tick marks, plus plot_function."""
from __future__ import annotations

from typing import Callable, Iterable

import numpy as np

from chalk.mobject import VMobject
from chalk.shapes import Line
from chalk.vgroup import VGroup


class Axes(VGroup):
    """2D axes.  Origin of the coordinate system is at world (0, 0) unless shifted.

    x_range and y_range are data ranges; width and height are world-unit extents.
    Call `to_point(x, y)` to map data coords to world coords.
    """

    def __init__(
        self,
        x_range: tuple[float, float] = (-5.0, 5.0),
        y_range: tuple[float, float] = (-3.0, 3.0),
        width:  float = 10.0,
        height: float = 6.0,
        x_step: float = 1.0,
        y_step: float = 1.0,
        color:  str   = "#9AA0A6",
        stroke_width: float = 2.0,
        tick_size:    float = 0.12,
    ) -> None:
        super().__init__()
        self.x_range = x_range
        self.y_range = y_range
        self._w = width
        self._h = height
        self._x_span = x_range[1] - x_range[0]
        self._y_span = y_range[1] - y_range[0]

        # Bounds of the drawn axes in world units, centered at origin.
        x_left  = -width / 2
        x_right =  width / 2
        y_bot   = -height / 2
        y_top   =  height / 2

        # x-axis runs at the y corresponding to data y=0, clamped into view.
        self._origin_world = self.to_point(0.0, 0.0) if self._contains(0.0, 0.0) \
            else ((x_left + x_right) / 2, (y_bot + y_top) / 2)

        axis_y_world = self._data_y_to_world(0.0) if y_range[0] <= 0 <= y_range[1] else y_bot
        axis_x_world = self._data_x_to_world(0.0) if x_range[0] <= 0 <= x_range[1] else x_left

        x_axis = Line((x_left, axis_y_world), (x_right, axis_y_world),
                      color=color, stroke_width=stroke_width)
        y_axis = Line((axis_x_world, y_bot), (axis_x_world, y_top),
                      color=color, stroke_width=stroke_width)
        self.submobjects.extend([x_axis, y_axis])

        # Ticks
        for xd in self._ticks(x_range[0], x_range[1], x_step):
            if abs(xd) < 1e-9:
                continue
            xw = self._data_x_to_world(xd)
            tick = Line((xw, axis_y_world - tick_size),
                        (xw, axis_y_world + tick_size),
                        color=color, stroke_width=stroke_width)
            self.submobjects.append(tick)
        for yd in self._ticks(y_range[0], y_range[1], y_step):
            if abs(yd) < 1e-9:
                continue
            yw = self._data_y_to_world(yd)
            tick = Line((axis_x_world - tick_size, yw),
                        (axis_x_world + tick_size, yw),
                        color=color, stroke_width=stroke_width)
            self.submobjects.append(tick)

    # ── Coordinate helpers ──────────────────────────────────────
    def _contains(self, x: float, y: float) -> bool:
        return self.x_range[0] <= x <= self.x_range[1] and \
               self.y_range[0] <= y <= self.y_range[1]

    def _data_x_to_world(self, x: float) -> float:
        t = (x - self.x_range[0]) / self._x_span
        return -self._w / 2 + t * self._w

    def _data_y_to_world(self, y: float) -> float:
        t = (y - self.y_range[0]) / self._y_span
        return -self._h / 2 + t * self._h

    def to_point(self, x: float, y: float) -> tuple[float, float]:
        return (self._data_x_to_world(x), self._data_y_to_world(y))

    @staticmethod
    def _ticks(lo: float, hi: float, step: float) -> Iterable[float]:
        n_start = int(np.ceil(lo / step))
        n_end   = int(np.floor(hi / step))
        for n in range(n_start, n_end + 1):
            yield n * step


def plot_function(
    axes: Axes,
    f: Callable[[float], float],
    x_start: float | None = None,
    x_end:   float | None = None,
    color:   str   = "#4FC3F7",
    stroke_width: float = 3.0,
    resolution:   int   = 60,
) -> VMobject:
    """Sample f over [x_start, x_end] and return a cubic-Bezier polyline VMobject
    in world coords relative to the axes (caller is responsible for any shift).
    """
    if x_start is None:
        x_start = axes.x_range[0]
    if x_end is None:
        x_end = axes.x_range[1]

    xs = np.linspace(x_start, x_end, resolution + 1)
    pts_world = np.array([axes.to_point(float(x), float(f(float(x)))) for x in xs])

    # Build a cubic Bezier chain: each segment becomes a line cubic
    # (handles at 1/3 and 2/3 of the segment).
    chain = []
    for i in range(resolution):
        a = pts_world[i]
        b = pts_world[i + 1]
        d = b - a
        chain.extend([a, a + d / 3, a + 2 * d / 3, b])

    m = VMobject(
        stroke_color=color,
        stroke_width=stroke_width,
        fill_color="#000000",
        fill_opacity=0.0,
        stroke_opacity=1.0,
    )
    m.points = np.array(chain, dtype=float)
    return m
