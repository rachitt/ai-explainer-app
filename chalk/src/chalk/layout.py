"""Relative-placement helpers.

`next_to(mob, anchor, direction, buff)` positions a VMobject or VGroup next to
another one with a fixed gap, so authors never do raw y = anchor_y - 0.7 math.
`align_center_x(mob, x)` horizontally aligns a mob's bbox center to a given x.

All offsets are in chalk world units.
"""
from __future__ import annotations

from typing import Literal, Union

import numpy as np

from chalk.mobject import VMobject
from chalk.vgroup import VGroup

Direction = Literal["UP", "DOWN", "LEFT", "RIGHT"]
Target = Union[VMobject, VGroup]


def _bbox(target: Target) -> tuple[float, float, float, float]:
    if isinstance(target, VGroup):
        return target.bbox()
    pts = target.points
    if len(pts) == 0:
        return (0.0, 0.0, 0.0, 0.0)
    return (float(pts[:, 0].min()), float(pts[:, 1].min()),
            float(pts[:, 0].max()), float(pts[:, 1].max()))


def _center(target: Target) -> tuple[float, float]:
    xmin, ymin, xmax, ymax = _bbox(target)
    return ((xmin + xmax) / 2, (ymin + ymax) / 2)


def _shift(target: Target, dx: float, dy: float) -> None:
    if isinstance(target, VGroup):
        target.shift(dx, dy)
    else:
        target.shift(dx, dy)


def next_to(
    mob: Target,
    anchor: Target,
    direction: Direction = "DOWN",
    buff: float = 0.25,
    align: Literal["center", "start", "end"] = "center",
) -> Target:
    """Place mob adjacent to anchor in the given direction with buff gap.

    align="center" keeps the cross-axis centered (default);
    "start" aligns to the left/top edge; "end" aligns to the right/bottom edge.
    """
    ax0, ay0, ax1, ay1 = _bbox(anchor)
    mx0, my0, mx1, my1 = _bbox(mob)
    mw = mx1 - mx0
    mh = my1 - my0
    mcx = (mx0 + mx1) / 2
    mcy = (my0 + my1) / 2

    if direction == "UP":
        target_cy = ay1 + buff + mh / 2
        if align == "center":
            target_cx = (ax0 + ax1) / 2
        elif align == "start":
            target_cx = ax0 + mw / 2
        else:
            target_cx = ax1 - mw / 2
    elif direction == "DOWN":
        target_cy = ay0 - buff - mh / 2
        if align == "center":
            target_cx = (ax0 + ax1) / 2
        elif align == "start":
            target_cx = ax0 + mw / 2
        else:
            target_cx = ax1 - mw / 2
    elif direction == "LEFT":
        target_cx = ax0 - buff - mw / 2
        if align == "center":
            target_cy = (ay0 + ay1) / 2
        elif align == "start":
            target_cy = ay1 - mh / 2
        else:
            target_cy = ay0 + mh / 2
    elif direction == "RIGHT":
        target_cx = ax1 + buff + mw / 2
        if align == "center":
            target_cy = (ay0 + ay1) / 2
        elif align == "start":
            target_cy = ay1 - mh / 2
        else:
            target_cy = ay0 + mh / 2
    else:
        raise ValueError(f"unknown direction: {direction!r}")

    _shift(mob, target_cx - mcx, target_cy - mcy)
    return mob


def labeled_box(
    label_latex: str,
    color: str,
    scale: float = 0.55,
    pad_x: float = 0.5,
    pad_y: float = 0.35,
    min_width:  float = 0.0,
    min_height: float = 0.0,
    fill_color:   str | None = None,
    fill_opacity: float = 0.0,
    stroke_width: float = 2.5,
    label_color:  str | None = None,
) -> tuple["VMobject", "VGroup"]:
    """Build a Rectangle sized to fit the MathTex label plus padding.

    Both the rectangle and the label are centered at origin; the caller is
    responsible for shifting them together (or wrap them in a VGroup).

    Returns (box, label).  Use `label_color=None` to inherit the box color.
    """
    from chalk.shapes import Rectangle
    from chalk.tex import MathTex

    lbl = MathTex(label_latex,
                  color=(label_color if label_color is not None else color),
                  scale=scale)
    xmin, ymin, xmax, ymax = lbl.bbox()
    w = max(xmax - xmin + 2 * pad_x, min_width)
    h = max(ymax - ymin + 2 * pad_y, min_height)

    box = Rectangle(
        width=w, height=h, color=color,
        fill_color=(fill_color if fill_color is not None else "#000000"),
        fill_opacity=fill_opacity,
        stroke_width=stroke_width,
    )
    # MathTex is created centered at origin; rectangle is centered at origin.
    # So they overlay correctly. Caller shifts both to the target position.
    return box, lbl


def place_in_zone(
    mob: Target,
    zone: tuple[float, float],
    x: float = 0.0,
) -> Target:
    """Center mob horizontally at x and vertically in the middle of the given zone."""
    ymin, ymax = zone
    zone_cy = (ymin + ymax) / 2
    cx, cy = _center(mob)
    _shift(mob, x - cx, zone_cy - cy)
    return mob
