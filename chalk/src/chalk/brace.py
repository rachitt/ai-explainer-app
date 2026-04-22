"""Brace: annotational curly brace around a target mobject."""
from __future__ import annotations

import math
from typing import Union

import numpy as np

from chalk.mobject import VMobject
from chalk.style import PRIMARY, SCALE_ANNOT
from chalk.vgroup import VGroup


def _brace_pts(length: float, tip_depth: float = 0.18, claw: float = 0.12) -> np.ndarray:
    """Build control points for a downward-facing brace of given `length`.

    The brace is centered at origin horizontally, with its claws at y=0 and
    its apex at y = -(tip_depth).

    Shape (from left to right):
      left claw → gentle arc in → center indent → apex → center indent → gentle arc out → right claw

    Uses 6 cubic Bezier segments.
    """
    hw = length / 2
    td = tip_depth
    cl = claw

    # Key y levels:
    # y = 0:     tips of both claws (connects to target bbox edge)
    # y = -cl:   base of claws, just before the arc
    # y = -td/2: midpoint of side arcs
    # y = -td:   apex y

    def seg(p0, p1, p2, p3):
        return [np.array(p0), np.array(p1), np.array(p2), np.array(p3)]

    pts = []

    # Segment 1: left claw — from left tip down
    pts += seg((-hw, 0), (-hw, -cl / 2), (-hw, -cl), (-hw + cl * 0.5, -cl))

    # Segment 2: sweep toward center-left
    pts += seg((-hw + cl * 0.5, -cl), (-hw / 2, -cl), (-hw / 4, -td + 0.04), (0, -td))

    # Segment 3: apex to center-right
    pts += seg((0, -td), (hw / 4, -td + 0.04), (hw / 2, -cl), (hw - cl * 0.5, -cl))

    # Segment 4: sweep out right
    pts += seg((hw - cl * 0.5, -cl), (hw, -cl), (hw, -cl / 2), (hw, 0))

    return np.array(pts, dtype=float)


def _rotate_points(pts: np.ndarray, angle: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    R = np.array([[c, -s], [s, c]])
    return pts @ R.T


_DIR_ANGLE = {"DOWN": 0.0, "UP": math.pi, "RIGHT": -math.pi / 2, "LEFT": math.pi / 2}
_DIR_AXIS = {"DOWN": (0, -1), "UP": (0, 1), "RIGHT": (1, 0), "LEFT": (-1, 0)}


class Brace(VMobject):
    """Curly brace annotating one side of a target mobject."""

    def __init__(
        self,
        target: Union[VMobject, VGroup],
        direction: str = "DOWN",
        buff: float = 0.2,
        color: str = PRIMARY,
        stroke_width: float = 2.0,
    ) -> None:
        super().__init__(stroke_color=color, stroke_width=stroke_width)
        self._direction = direction
        self._tip: np.ndarray | None = None

        if isinstance(target, VGroup):
            bb = target.bbox()
        else:
            pts = target.points
            bb = (float(pts[:, 0].min()), float(pts[:, 1].min()),
                  float(pts[:, 0].max()), float(pts[:, 1].max()))

        xmin, ymin, xmax, ymax = bb
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2

        if direction == "DOWN":
            length = xmax - xmin
            raw = _brace_pts(length)
            offset = np.array([cx, ymin - buff])
            self._tip = np.array([cx, ymin - buff - 0.18])
        elif direction == "UP":
            length = xmax - xmin
            raw = _brace_pts(length)
            raw = _rotate_points(raw, math.pi)
            offset = np.array([cx, ymax + buff])
            self._tip = np.array([cx, ymax + buff + 0.18])
        elif direction == "LEFT":
            length = ymax - ymin
            raw = _brace_pts(length)
            raw = _rotate_points(raw, math.pi / 2)
            offset = np.array([xmin - buff, cy])
            self._tip = np.array([xmin - buff - 0.18, cy])
        elif direction == "RIGHT":
            length = ymax - ymin
            raw = _brace_pts(length)
            raw = _rotate_points(raw, -math.pi / 2)
            offset = np.array([xmax + buff, cy])
            self._tip = np.array([xmax + buff + 0.18, cy])
        else:
            raise ValueError(f"Unknown direction: {direction!r}")

        self.points = raw + offset

    def get_tip(self) -> tuple[float, float]:
        """Return the world (x, y) of the brace apex."""
        if self._tip is None:
            return (0.0, 0.0)
        return (float(self._tip[0]), float(self._tip[1]))
