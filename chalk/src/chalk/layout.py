"""Relative-placement helpers.

`next_to(mob, anchor, direction, buff)` positions a VMobject or VGroup next to
another one with a fixed gap, so authors never do raw y = anchor_y - 0.7 math.
`align_center_x(mob, x)` horizontally aligns a mob's bbox center to a given x.

All offsets are in chalk world units.
"""
from __future__ import annotations

import warnings
from typing import Literal, Union

import numpy as np

from chalk.mobject import VMobject
from chalk.style import SCALE_ANNOT
from chalk.vgroup import VGroup

Direction = Literal["UP", "DOWN", "LEFT", "RIGHT"]
Target = Union[VMobject, VGroup]


class LayoutOverlapWarning(UserWarning):
    """Warning raised when layout mobjects are closer than the requested gap."""


class LayoutOverlapError(ValueError):
    """Error raised when layout mobjects are closer than the requested gap."""


def check_no_overlap(
    mobjects,
    min_sep: float,
    raise_on_fail: bool = False,
) -> list[tuple[int, int, float]]:
    """Check pairwise center-distance between positioned mobjects.

    Each mobject must expose a .position attribute (np.ndarray of 2 floats).
    Mobjects without .position are skipped.
    """
    positioned: list[tuple[int, np.ndarray]] = []
    for i, mob in enumerate(mobjects):
        if not hasattr(mob, "position"):
            continue
        positioned.append((i, np.asarray(mob.position, dtype=float)))

    overlaps: list[tuple[int, int, float]] = []
    for a_idx, a_pos in positioned:
        for b_idx, b_pos in positioned:
            if b_idx <= a_idx:
                continue
            dist = float(np.linalg.norm(a_pos - b_pos))
            if dist < min_sep:
                overlaps.append((a_idx, b_idx, dist))

    if overlaps:
        msg = (
            f"{len(overlaps)} layout overlap(s): "
            + ", ".join(
                f"{i}-{j} distance {dist:.3f} < {min_sep:.3f}"
                for i, j, dist in overlaps
            )
        )
        if raise_on_fail:
            raise LayoutOverlapError(msg)
        warnings.warn(msg, LayoutOverlapWarning, stacklevel=2)

    return overlaps


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


def _ray_bbox_exit(
    cx: float, cy: float, ux: float, uy: float,
    xmin: float, ymin: float, xmax: float, ymax: float,
) -> tuple[float, float]:
    """From center (cx, cy), shoot a ray along unit vector (ux, uy); return
    the point where it first crosses the axis-aligned bbox boundary.
    """
    ts: list[float] = []
    if ux > 1e-9:
        ts.append((xmax - cx) / ux)
    elif ux < -1e-9:
        ts.append((xmin - cx) / ux)
    if uy > 1e-9:
        ts.append((ymax - cy) / uy)
    elif uy < -1e-9:
        ts.append((ymin - cy) / uy)
    t = min(ts) if ts else 0.0
    return (cx + t * ux, cy + t * uy)


def arrow_between(
    source: Target,
    target: Target,
    buff:   float = 0.15,
    color:  str   = "#E8EAED",
    stroke_width: float = 2.0,
    head_length:  float = 0.25,
    head_width:   float = 0.22,
    shaft_width:  float = 0.06,
):
    """Build an Arrow from source to target, anchored at their bbox edges with
    `buff` gap on each side. Works for any VMobject / VGroup combination —
    circles, rectangles, MathTex labels, etc.
    """
    from chalk.shapes import Arrow
    sx0, sy0, sx1, sy1 = _bbox(source)
    tx0, ty0, tx1, ty1 = _bbox(target)
    scx, scy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    tcx, tcy = (tx0 + tx1) / 2, (ty0 + ty1) / 2

    dx, dy = tcx - scx, tcy - scy
    mag = (dx * dx + dy * dy) ** 0.5
    if mag < 1e-9:
        raise ValueError("source and target share the same center; cannot draw arrow")
    ux, uy = dx / mag, dy / mag

    s_exit  = _ray_bbox_exit(scx, scy,  ux,  uy, sx0, sy0, sx1, sy1)
    t_entry = _ray_bbox_exit(tcx, tcy, -ux, -uy, tx0, ty0, tx1, ty1)

    start = (s_exit[0] + buff * ux,  s_exit[1] + buff * uy)
    end   = (t_entry[0] - buff * ux, t_entry[1] - buff * uy)

    return Arrow(
        start, end,
        color=color, stroke_width=stroke_width,
        head_length=head_length, head_width=head_width, shaft_width=shaft_width,
    )


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


def brace_label(
    target: Target,
    tex: str,
    direction: str = "DOWN",
    buff: float = 0.2,
    color: str = "#E8EAED",
    scale: float = SCALE_ANNOT,
) -> "tuple[object, VGroup]":
    """Build a Brace + MathTex label positioned at the brace's tip.

    Returns (brace, label).  Both are ready to add to a Scene.
    """
    from chalk.brace import Brace
    from chalk.tex import MathTex

    brace = Brace(target, direction=direction, buff=buff, color=color)
    tip = brace.get_tip()

    lbl = MathTex(tex, color=color, scale=scale)
    lbl_bb = lbl.bbox()
    lbl_cx = (lbl_bb[0] + lbl_bb[2]) / 2
    lbl_cy = (lbl_bb[1] + lbl_bb[3]) / 2

    extra_buff = 0.15
    if direction == "DOWN":
        lbl.shift(tip[0] - lbl_cx, tip[1] - extra_buff - (lbl_bb[3] - lbl_bb[1]) / 2 - lbl_cy)
    elif direction == "UP":
        lbl.shift(tip[0] - lbl_cx, tip[1] + extra_buff + (lbl_bb[3] - lbl_bb[1]) / 2 - lbl_cy)
    elif direction == "LEFT":
        lbl.shift(tip[0] - extra_buff - (lbl_bb[2] - lbl_bb[0]) / 2 - lbl_cx, tip[1] - lbl_cy)
    elif direction == "RIGHT":
        lbl.shift(tip[0] + extra_buff + (lbl_bb[2] - lbl_bb[0]) / 2 - lbl_cx, tip[1] - lbl_cy)

    return brace, lbl


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
