"""chalk.physics — domain primitive kit for classical mechanics scenes.

Pure compositions of C1 primitives. No new renderer features.

Exports: Spring, Pendulum, Mass, Vector, FreeBody
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from chalk.vgroup import VGroup
from chalk.style import PRIMARY, YELLOW, BLUE, RED_FILL, GREY, SCALE_LABEL, SCALE_ANNOT

if TYPE_CHECKING:
    from chalk.value_tracker import ValueTracker


class Spring(VGroup):
    """Zigzag spring drawn between two world-space points.

    Rendered as a VGroup of Line segments: two short connectors at each end
    and 2*coils zigzag strokes between them.
    """

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        coils: int = 6,
        amplitude: float = 0.2,
        color: str = PRIMARY,
        stroke_width: float = 2.0,
    ) -> None:
        from chalk.shapes import Line

        p0 = np.array(start, dtype=float)
        p1 = np.array(end, dtype=float)
        chord = p1 - p0
        length = float(np.linalg.norm(chord))

        if length < 1e-9:
            super().__init__()
            return

        u = chord / length
        perp = np.array([-u[1], u[0]])
        connector = min(0.12 * length, 0.3)
        middle = length - 2 * connector

        # Build polyline vertices
        vertices: list[np.ndarray] = [p0, p0 + connector * u]
        n_peaks = 2 * coils
        for i in range(n_peaks):
            t = (i + 0.5) / n_peaks
            sign = 1.0 if i % 2 == 0 else -1.0
            pt = p0 + connector * u + t * middle * u + sign * amplitude * perp
            vertices.append(pt)
        vertices.append(p1 - connector * u)
        vertices.append(p1)

        lines = [
            Line(
                (float(vertices[i][0]), float(vertices[i][1])),
                (float(vertices[i + 1][0]), float(vertices[i + 1][1])),
                color=color,
                stroke_width=stroke_width,
            )
            for i in range(len(vertices) - 1)
        ]
        super().__init__(*lines)


def Pendulum(
    pivot: tuple[float, float],
    length: float,
    angle_tracker: "ValueTracker",
    rod_color: str = PRIMARY,
    bob_color: str = BLUE,
    bob_radius: float = 0.2,
) -> "AlwaysRedraw":
    """Rod + bob pendulum driven by angle_tracker (radians from vertical).

    Returns an AlwaysRedraw VGroup — add it to the scene; it updates every frame.
    """
    from chalk.redraw import always_redraw
    from chalk.shapes import Line, Circle

    px, py = float(pivot[0]), float(pivot[1])

    def _build() -> VGroup:
        angle = angle_tracker.get_value()
        bx = px + length * math.sin(angle)
        by = py - length * math.cos(angle)
        rod = Line((px, py), (bx, by), color=rod_color, stroke_width=3.0)
        bob = Circle(radius=bob_radius, color=bob_color, fill_color=bob_color, fill_opacity=1.0)
        bob.shift(bx, by)
        return VGroup(rod, bob)

    return always_redraw(_build)


class Mass(VGroup):
    """Labeled box representing a physical mass, with an optional weight arrow.

    Mass is centered at position. Call shift()/move_to() on the VGroup after
    creation to reposition the whole assembly.
    """

    def __init__(
        self,
        position: tuple[float, float] = (0.0, 0.0),
        label: str = "m",
        color: str = BLUE,
        show_weight: bool = True,
    ) -> None:
        from chalk.layout import labeled_box
        from chalk.shapes import Arrow

        box, lbl = labeled_box(label, color=color, scale=SCALE_LABEL)
        box.shift(position[0], position[1])
        lbl.move_to(position[0], position[1])

        mobs: list = [box, lbl]

        if show_weight:
            # Short downward arrow beneath the box bbox
            half_h = (box.points[:, 1].max() - box.points[:, 1].min()) / 2
            wy_start = position[1] - half_h - 0.1
            wy_end = wy_start - 0.55
            weight_arrow = Arrow(
                (position[0], wy_start),
                (position[0], wy_end),
                color=RED_FILL,
                head_length=0.15,
                head_width=0.12,
                shaft_width=0.04,
            )
            mobs.append(weight_arrow)

        super().__init__(*mobs)


class Vector(VGroup):
    """Directed arrow with an optional LaTeX label anchored near the tip.

    Useful in force diagrams where each force needs a symbol.
    """

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        label: str = "",
        color: str = YELLOW,
    ) -> None:
        from chalk.shapes import Arrow
        from chalk.tex import MathTex

        arrow = Arrow(start, end, color=color)
        mobs: list = [arrow]

        if label:
            p0 = np.array(start, dtype=float)
            p1 = np.array(end, dtype=float)
            direction = p1 - p0
            norm = float(np.linalg.norm(direction))
            lbl = MathTex(label, color=color, scale=SCALE_LABEL)
            if norm > 1e-9:
                perp = np.array([-direction[1], direction[0]]) / norm
                label_pos = p1 + 0.3 * perp + 0.05 * direction / norm
                lbl.move_to(float(label_pos[0]), float(label_pos[1]))
            else:
                lbl.move_to(float(p1[0]), float(p1[1]) + 0.35)
            mobs.append(lbl)

        super().__init__(*mobs)


class FreeBody(VGroup):
    """Mass box at center with force arrows radiating in specified directions.

    forces: list of (magnitude, direction_deg, label) tuples.
    direction_deg=90 → upward, 0 → rightward, 270 → downward, etc.
    Magnitude scales the arrow length.
    """

    def __init__(
        self,
        label: str = "m",
        forces: "list[tuple[float, float, str]] | None" = None,
        color: str = BLUE,
        force_color: str = YELLOW,
    ) -> None:
        from chalk.layout import labeled_box
        from chalk.shapes import Arrow
        from chalk.tex import MathTex

        box, lbl = labeled_box(label, color=color, scale=SCALE_LABEL)
        mobs: list = [box, lbl]

        for magnitude, direction_deg, force_label in (forces or []):
            angle_rad = math.radians(direction_deg)
            dx = magnitude * math.cos(angle_rad)
            dy = magnitude * math.sin(angle_rad)
            force_arrow = Arrow(
                (0.0, 0.0), (dx, dy),
                color=force_color,
                head_length=0.15,
                head_width=0.12,
                shaft_width=0.04,
            )
            mobs.append(force_arrow)
            if force_label:
                perp_x = -math.sin(angle_rad)
                perp_y = math.cos(angle_rad)
                tip_x = dx + 0.28 * perp_x
                tip_y = dy + 0.28 * perp_y
                f_lbl = MathTex(force_label, color=force_color, scale=SCALE_ANNOT)
                f_lbl.move_to(tip_x, tip_y)
                mobs.append(f_lbl)

        super().__init__(*mobs)
