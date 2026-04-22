"""NumberLine and NumberPlane coordinate-system primitives."""
from __future__ import annotations

import math
from typing import Union

from chalk.mobject import VMobject
from chalk.shapes import Line
from chalk.style import GREY, TRACK, SCALE_ANNOT
from chalk.vgroup import VGroup


def _fmt(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return f"{v:.2g}"


class NumberLine(VGroup):
    """Horizontal number line centered at world origin.

    x_range = (min, max, step).  `length` is the world-unit extent.
    n2p/p2n convert between data coordinates and world (x, y) tuples.
    """

    def __init__(
        self,
        x_range: tuple[float, float, float] = (-5.0, 5.0, 1.0),
        length: float = 10.0,
        include_tip: bool = False,
        include_numbers: bool = False,
        label_direction: str = "DOWN",
        color: str = GREY,
        number_scale: float = SCALE_ANNOT,
        tick_size: float = 0.1,
    ) -> None:
        super().__init__()
        self.x_min, self.x_max, self.x_step = x_range
        self.length = length
        self._color = color

        # Main axis line
        x0 = self._n2world(self.x_min)
        x1 = self._n2world(self.x_max)
        self.add(Line((x0, 0.0), (x1, 0.0), color=color, stroke_width=2.0))

        # Tick marks
        v = self.x_min
        while v <= self.x_max + 1e-9:
            wx = self._n2world(v)
            self.add(Line((wx, -tick_size / 2), (wx, tick_size / 2),
                          color=color, stroke_width=1.5))
            v = round(v + self.x_step, 10)

        # Optional number labels
        if include_numbers:
            from chalk.tex import MathTex
            v = self.x_min
            while v <= self.x_max + 1e-9:
                wx = self._n2world(v)
                lbl = MathTex(_fmt(v), color=color, scale=number_scale)
                lbl_cx, lbl_cy = self._label_offset(lbl, label_direction, tick_size)
                lbl.shift(wx + lbl_cx, lbl_cy)
                self.add(lbl)
                v = round(v + self.x_step, 10)

    def _n2world(self, n: float) -> float:
        span = self.x_max - self.x_min
        if span < 1e-12:
            return 0.0
        return (n - self.x_min) / span * self.length - self.length / 2

    def _label_offset(self, lbl: VGroup, direction: str, tick_size: float) -> tuple[float, float]:
        from chalk.vgroup import VGroup as VG
        bb = lbl.bbox() if isinstance(lbl, VG) else (0, 0, 0, 0)
        h = bb[3] - bb[1]
        buff = 0.15
        if direction == "DOWN":
            return (0.0, -tick_size / 2 - buff - h / 2)
        elif direction == "UP":
            return (0.0, tick_size / 2 + buff + h / 2)
        return (0.0, -tick_size / 2 - buff - h / 2)

    def n2p(self, number: float) -> tuple[float, float]:
        """Map data value to world (x, y) point on the line."""
        return (self._n2world(number), 0.0)

    def p2n(self, point: tuple[float, float]) -> float:
        """Map world point back to data value."""
        wx = point[0]
        span = self.x_max - self.x_min
        if self.length < 1e-12:
            return self.x_min
        return self.x_min + (wx + self.length / 2) / self.length * span


class NumberPlane(VGroup):
    """2D coordinate plane with background grid lines and optional axes.

    c2p(x, y) → world (px, py).  p2c((px, py)) → data (x, y).
    """

    def __init__(
        self,
        x_range: tuple[float, float, float] = (-7.0, 7.0, 1.0),
        y_range: tuple[float, float, float] = (-4.0, 4.0, 1.0),
        background_line_style: dict | None = None,
        axis_config: dict | None = None,
    ) -> None:
        super().__init__()
        self.x_min, self.x_max, self.x_step = x_range
        self.y_min, self.y_max, self.y_step = y_range

        # World extents (fill the standard chalk frame)
        self._x_length = self.x_max - self.x_min
        self._y_length = self.y_max - self.y_min

        style = background_line_style or {}
        grid_color = style.get("stroke_color", TRACK)
        grid_width = float(style.get("stroke_width", 1.0))
        ax_cfg = axis_config or {}
        ax_color = ax_cfg.get("color", GREY)

        # Vertical grid lines
        x = self.x_min
        while x <= self.x_max + 1e-9:
            px = self._x2world(x)
            py0 = self._y2world(self.y_min)
            py1 = self._y2world(self.y_max)
            lw = 2.0 if abs(x) < 1e-9 else grid_width
            col = ax_color if abs(x) < 1e-9 else grid_color
            self.add(Line((px, py0), (px, py1), color=col, stroke_width=lw))
            x = round(x + self.x_step, 10)

        # Horizontal grid lines
        y = self.y_min
        while y <= self.y_max + 1e-9:
            px0 = self._x2world(self.x_min)
            px1 = self._x2world(self.x_max)
            py = self._y2world(y)
            lw = 2.0 if abs(y) < 1e-9 else grid_width
            col = ax_color if abs(y) < 1e-9 else grid_color
            self.add(Line((px0, py), (px1, py), color=col, stroke_width=lw))
            y = round(y + self.y_step, 10)

    def _x2world(self, x: float) -> float:
        span = self.x_max - self.x_min
        return (x - self.x_min) / span * self._x_length - self._x_length / 2 if span > 1e-12 else 0.0

    def _y2world(self, y: float) -> float:
        span = self.y_max - self.y_min
        return (y - self.y_min) / span * self._y_length - self._y_length / 2 if span > 1e-12 else 0.0

    def c2p(self, x: float, y: float) -> tuple[float, float]:
        return (self._x2world(x), self._y2world(y))

    def p2c(self, p: tuple[float, float]) -> tuple[float, float]:
        px, py = p
        span_x = self.x_max - self.x_min
        span_y = self.y_max - self.y_min
        data_x = (self.x_min + (px + self._x_length / 2) / self._x_length * span_x
                  if self._x_length > 1e-12 else self.x_min)
        data_y = (self.y_min + (py + self._y_length / 2) / self._y_length * span_y
                  if self._y_length > 1e-12 else self.y_min)
        return (data_x, data_y)
