"""chalk.circuits — domain primitive kit for circuit-diagram scenes.

Pure compositions of C1 primitives. No new renderer features.

Exports: Resistor, Battery, Capacitor, Inductor, Switch, Ground,
         Wire, SeriesLoop, CurrentFlow, VoltageLabel, KirchhoffDemo
"""
from __future__ import annotations

import math

import numpy as np

from chalk.redraw import AlwaysRedraw
from chalk.style import BLUE, GREEN, GREY, PRIMARY, SCALE_ANNOT, SCALE_LABEL, YELLOW
from chalk.value_tracker import ValueTracker
from chalk.vgroup import VGroup


def _unit_and_perp(start: np.ndarray, end: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Return (unit, perp, length) for a segment."""
    chord = end - start
    length = float(np.linalg.norm(chord))
    if length < 1e-9:
        return np.array([1.0, 0.0]), np.array([0.0, 1.0]), 0.0
    u = chord / length
    perp = np.array([-u[1], u[0]])
    return u, perp, length


def _lines_from_vertices(vertices: list[np.ndarray], color: str, stroke_width: float) -> list:
    from chalk.shapes import Line
    return [
        Line(
            (float(vertices[i][0]), float(vertices[i][1])),
            (float(vertices[i + 1][0]), float(vertices[i + 1][1])),
            color=color, stroke_width=stroke_width,
        )
        for i in range(len(vertices) - 1)
    ]


def _line_between_points(start: np.ndarray, end: np.ndarray, color: str, stroke_width: float):
    from chalk.shapes import Line
    return Line(
        (float(start[0]), float(start[1])),
        (float(end[0]), float(end[1])),
        color=color, stroke_width=stroke_width,
    )


class Resistor(VGroup):
    """American-style zigzag resistor from start to end.

    zigzag_count full teeth; each tooth alternates ±amplitude from the axis.
    """

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        zigzag_count: int = 4,
        amplitude: float = 0.12,
        color: str = PRIMARY,
        stroke_width: float = 2.0,
    ) -> None:
        p0 = np.array(start, dtype=float)
        p1 = np.array(end, dtype=float)
        self.start = p0.copy()
        self.end = p1.copy()
        u, perp, length = _unit_and_perp(p0, p1)
        if length < 1e-9:
            super().__init__()
            return

        connector = min(0.15 * length, 0.25)
        body = length - 2 * connector
        n_teeth = 2 * zigzag_count

        vertices = [p0, p0 + connector * u]
        for i in range(n_teeth):
            t = (i + 0.5) / n_teeth
            sign = 1.0 if i % 2 == 0 else -1.0
            vertices.append(p0 + connector * u + t * body * u + sign * amplitude * perp)
        vertices.append(p1 - connector * u)
        vertices.append(p1)

        super().__init__(*_lines_from_vertices(vertices, color, stroke_width))


class Battery(VGroup):
    """Single-cell battery symbol between start and end.

    polarity="right" → positive plate (long line) is toward end.
    polarity="left"  → positive plate is toward start.
    """

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        polarity: str = "right",
        color: str = GREEN,
        stroke_width: float = 2.0,
    ) -> None:
        from chalk.shapes import Line

        p0 = np.array(start, dtype=float)
        p1 = np.array(end, dtype=float)
        self.start = p0.copy()
        self.end = p1.copy()
        u, perp, length = _unit_and_perp(p0, p1)
        if length < 1e-9:
            super().__init__()
            return

        mid = (p0 + p1) / 2
        gap = min(0.08, 0.04 * length)
        pos_half = 0.2   # half-height of positive (long) plate
        neg_half = 0.12  # half-height of negative (short) plate

        if polarity == "right":
            neg_c = mid - gap * u
            pos_c = mid + gap * u
        else:
            pos_c = mid - gap * u
            neg_c = mid + gap * u

        wire_l = Line(tuple(p0), (float(neg_c[0]), float(neg_c[1])),
                      color=color, stroke_width=stroke_width)
        wire_r = Line((float(pos_c[0]), float(pos_c[1])), tuple(p1),
                      color=color, stroke_width=stroke_width)

        neg_plate = Line(
            (float(neg_c[0] + neg_half * perp[0]), float(neg_c[1] + neg_half * perp[1])),
            (float(neg_c[0] - neg_half * perp[0]), float(neg_c[1] - neg_half * perp[1])),
            color=color, stroke_width=stroke_width * 2.5,
        )
        pos_plate = Line(
            (float(pos_c[0] + pos_half * perp[0]), float(pos_c[1] + pos_half * perp[1])),
            (float(pos_c[0] - pos_half * perp[0]), float(pos_c[1] - pos_half * perp[1])),
            color=color, stroke_width=stroke_width,
        )

        super().__init__(wire_l, wire_r, neg_plate, pos_plate)


class Capacitor(VGroup):
    """Capacitor symbol: two equal parallel plates separated by a gap."""

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        plate_half: float = 0.2,
        color: str = BLUE,
        stroke_width: float = 2.0,
    ) -> None:
        from chalk.shapes import Line

        p0 = np.array(start, dtype=float)
        p1 = np.array(end, dtype=float)
        self.start = p0.copy()
        self.end = p1.copy()
        u, perp, length = _unit_and_perp(p0, p1)
        if length < 1e-9:
            super().__init__()
            return

        mid = (p0 + p1) / 2
        gap = min(0.1, 0.05 * length)
        c1 = mid - gap * u
        c2 = mid + gap * u

        wire_l = Line(tuple(p0), (float(c1[0]), float(c1[1])),
                      color=color, stroke_width=stroke_width)
        wire_r = Line((float(c2[0]), float(c2[1])), tuple(p1),
                      color=color, stroke_width=stroke_width)

        def _plate(center: np.ndarray) -> Line:
            top = center + plate_half * perp
            bot = center - plate_half * perp
            return Line(
                (float(top[0]), float(top[1])),
                (float(bot[0]), float(bot[1])),
                color=color, stroke_width=stroke_width * 1.8,
            )

        super().__init__(wire_l, wire_r, _plate(c1), _plate(c2))


class Inductor(VGroup):
    """Inductor: series of semicircular bumps above the wire axis."""

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        coils: int = 3,
        color: str = PRIMARY,
        stroke_width: float = 2.0,
    ) -> None:
        from chalk.shapes import ArcBetweenPoints, Line

        p0 = np.array(start, dtype=float)
        p1 = np.array(end, dtype=float)
        self.start = p0.copy()
        self.end = p1.copy()
        u, _perp, length = _unit_and_perp(p0, p1)
        if length < 1e-9:
            super().__init__()
            return

        connector = min(0.12 * length, 0.2)
        body = length - 2 * connector
        coil_w = body / coils

        mobs = []
        # Left connector
        mobs.append(Line(tuple(p0), tuple(p0 + connector * u),
                         color=color, stroke_width=stroke_width))
        # Coil bumps (arcs above the axis)
        for i in range(coils):
            arc_start = p0 + connector * u + i * coil_w * u
            arc_end = arc_start + coil_w * u
            mobs.append(ArcBetweenPoints(
                (float(arc_start[0]), float(arc_start[1])),
                (float(arc_end[0]), float(arc_end[1])),
                angle=-math.pi,  # bump on the perp side
                color=color, stroke_width=stroke_width,
            ))
        # Right connector
        mobs.append(Line(tuple(p1 - connector * u), tuple(p1),
                         color=color, stroke_width=stroke_width))

        super().__init__(*mobs)


class Switch(VGroup):
    """Simple SPST switch symbol between start and end.

    open=True → gap + angled lever; open=False → closed (straight line).
    """

    def __init__(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        open: bool = True,
        color: str = PRIMARY,
        stroke_width: float = 2.0,
    ) -> None:
        from chalk.shapes import Dot, Line

        p0 = np.array(start, dtype=float)
        p1 = np.array(end, dtype=float)
        self.start = p0.copy()
        self.end = p1.copy()
        u, perp, length = _unit_and_perp(p0, p1)
        if length < 1e-9:
            super().__init__()
            return

        connector = min(0.2 * length, 0.4)
        pivot = p0 + connector * u
        contact = p1 - connector * u

        wire_l = Line(tuple(p0), (float(pivot[0]), float(pivot[1])),
                      color=color, stroke_width=stroke_width)
        wire_r = Line((float(contact[0]), float(contact[1])), tuple(p1),
                      color=color, stroke_width=stroke_width)
        dot_l = Dot((float(pivot[0]), float(pivot[1])), radius=0.06, color=color)
        dot_r = Dot((float(contact[0]), float(contact[1])), radius=0.06, color=color)

        if open:
            # Lever angled ~30° above axis from pivot
            lever_end = pivot + (contact - pivot) * 0.9 + 0.25 * perp
            lever = Line(
                (float(pivot[0]), float(pivot[1])),
                (float(lever_end[0]), float(lever_end[1])),
                color=color, stroke_width=stroke_width,
            )
            super().__init__(wire_l, wire_r, dot_l, dot_r, lever)
        else:
            bridge = Line(
                (float(pivot[0]), float(pivot[1])),
                (float(contact[0]), float(contact[1])),
                color=color, stroke_width=stroke_width,
            )
            super().__init__(wire_l, wire_r, dot_l, dot_r, bridge)


class Ground(VGroup):
    """Standard three-line ground symbol at a point, pointing in direction."""

    def __init__(
        self,
        point: tuple[float, float],
        color: str = GREY,
        stroke_width: float = 2.0,
    ) -> None:
        from chalk.shapes import Line

        x, y = float(point[0]), float(point[1])
        self.point = np.array(point, dtype=float)
        lines = [
            Line(
                (x - 0.28, y),
                (x + 0.28, y),
                color=color,
                stroke_width=stroke_width,
            ),
            Line(
                (x - 0.18, y - 0.10),
                (x + 0.18, y - 0.10),
                color=color,
                stroke_width=stroke_width,
            ),
            Line(
                (x - 0.08, y - 0.20),
                (x + 0.08, y - 0.20),
                color=color,
                stroke_width=stroke_width,
            ),
        ]
        super().__init__(*lines)


class Wire(VGroup):
    """Multi-segment polyline connecting waypoints.

    Provides point_at_fraction(t) for use with CurrentFlow.
    """

    def __init__(
        self,
        *points: tuple[float, float],
        breaks: list[object] | tuple[object, ...] | None = None,
        color: str = GREY,
        stroke_width: float = 2.0,
    ) -> None:
        self.breaks = list(breaks or ())
        self.waypoints = [np.array(p, dtype=float) for p in points]
        self.segments = [
            (self.waypoints[i].copy(), self.waypoints[i + 1].copy())
            for i in range(len(self.waypoints) - 1)
        ]
        for comp in self.breaks:
            self._apply_break(comp)
        lines = [
            _line_between_points(a, b, color, stroke_width)
            for a, b in self.segments
            if float(np.linalg.norm(b - a)) >= 1e-9
        ]
        super().__init__(*lines)

    def _apply_break(self, comp: object) -> None:
        s = np.array(comp.start, dtype=float)
        e = np.array(comp.end, dtype=float)

        for i, (a, b) in enumerate(self.segments):
            ts = self._segment_parameter(a, b, s)
            te = self._segment_parameter(a, b, e)
            if ts is None or te is None:
                continue

            first, second = (s, e) if ts <= te else (e, s)
            replacement = []
            if float(np.linalg.norm(first - a)) >= 1e-9:
                replacement.append((a, first.copy()))
            if float(np.linalg.norm(b - second)) >= 1e-9:
                replacement.append((second.copy(), b))
            self.segments[i:i + 1] = replacement
            return

        raise ValueError(f"break component endpoints {s},{e} do not lie on any wire segment")

    @staticmethod
    def _segment_parameter(a: np.ndarray, b: np.ndarray, p: np.ndarray) -> float | None:
        v = b - a
        length_sq = float(np.dot(v, v))
        if length_sq < 1e-18:
            return None
        rel = p - a
        cross = float(v[0] * rel[1] - v[1] * rel[0])
        length = math.sqrt(length_sq)
        if abs(cross) > 1e-6 * length:
            return None
        t = float(np.dot(rel, v) / length_sq)
        if t < -1e-6 or t > 1.0 + 1e-6:
            return None
        return max(0.0, min(1.0, t))

    def point_at_fraction(self, t: float) -> np.ndarray:
        """World position at fraction t (0=start, 1=end) of total wire length."""
        t = max(0.0, min(1.0, t))
        if not self.segments:
            return self.waypoints[0].copy() if self.waypoints else np.zeros(2)

        seg_lengths = [float(np.linalg.norm(b - a)) for a, b in self.segments]
        total = sum(seg_lengths)
        if total < 1e-9:
            return self.segments[0][0].copy()

        target = t * total
        cumlen = 0.0
        for i, seg_len in enumerate(seg_lengths):
            a, b = self.segments[i]
            if cumlen + seg_len >= target - 1e-9:
                if seg_len < 1e-9:
                    return a.copy()
                local_t = (target - cumlen) / seg_len
                return a + local_t * (b - a)
            cumlen += seg_len
        return self.segments[-1][1].copy()


def SeriesLoop(
    components: list,
    width: float = 8.0,
    height: float = 3.0,
    wire_color: str = GREY,
    stroke_width: float = 2.0,
) -> VGroup:
    """Rectangular wire loop around N<=4 series components.

    Caller positions components on the perimeter (top/bottom edges typical).
    Returns VGroup(wire, *components) where the wire auto-splits at each
    component's .start/.end via Wire(breaks=components).

    Raises NotImplementedError for N > 4.
    """
    if len(components) > 4:
        raise NotImplementedError("SeriesLoop supports at most 4 components")
    hw, hh = width / 2.0, height / 2.0
    tl = (-hw, hh)
    tr = (hw, hh)
    br = (hw, -hh)
    bl = (-hw, -hh)
    wire = Wire(
        tl, tr, br, bl, tl,
        color=wire_color,
        stroke_width=stroke_width,
        breaks=list(components),
    )
    return VGroup(wire, *components)


class CurrentFlow(AlwaysRedraw):
    """Stream of charge-carrier dots animated along a Wire path.

    The phase is driven by an external ValueTracker (0→1 = one full loop).
    Use ChangeValue(flow.phase, 1.0, run_time=t) to animate.

    rate_tracker is optional: if provided, the class auto-integrates speed
    from the tracker each refresh. If omitted, control phase_tracker directly.
    """

    def __init__(
        self,
        wire: Wire,
        charge_count: int = 8,
        color: str = YELLOW,
    ) -> None:
        self._wire = wire
        self._charge_count = charge_count
        self._color = color
        self.phase = ValueTracker(0.0)
        super().__init__(self._build)

    def _build(self) -> VGroup:
        from chalk.shapes import Dot

        phase = self.phase.get_value() % 1.0
        dots = []
        for i in range(self._charge_count):
            t = (i / self._charge_count + phase) % 1.0
            pos = self._wire.point_at_fraction(t)
            dots.append(Dot(
                point=(float(pos[0]), float(pos[1])),
                radius=0.05,
                color=self._color,
            ))
        return VGroup(*dots)


def VoltageLabel(
    across: tuple[tuple[float, float], tuple[float, float]],
    value: str,
    color: str = YELLOW,
    side: str = "UP",
) -> VGroup:
    """Bracketed voltage annotation across two wire endpoints.

    Draws an arrow from the - terminal to the + terminal, with the value label
    centered above/below. side="UP"|"DOWN" picks which side of the segment.
    """
    from chalk.shapes import Arrow
    from chalk.tex import MathTex

    p0 = np.array(across[0], dtype=float)
    p1 = np.array(across[1], dtype=float)
    u, perp, length = _unit_and_perp(p0, p1)
    sign = 1.0 if side == "UP" else -1.0
    offset = max(0.45, 0.5 * length) + 0.3

    a_start = p0 + sign * offset * perp
    a_end = p1 + sign * offset * perp
    mid = (a_start + a_end) / 2

    arrow = Arrow(
        (float(a_start[0]), float(a_start[1])),
        (float(a_end[0]), float(a_end[1])),
        color=color, head_length=0.15, head_width=0.12, shaft_width=0.04,
    )
    lbl = MathTex(value, color=color, scale=SCALE_LABEL)
    lbl_pos = mid + sign * 0.35 * perp
    lbl.move_to(float(lbl_pos[0]), float(lbl_pos[1]))

    plus = MathTex(r"+", color=color, scale=SCALE_ANNOT)
    minus = MathTex(r"-", color=color, scale=SCALE_ANNOT)
    plus_pos = a_end + 0.15 * u
    minus_pos = a_start - 0.15 * u
    plus.move_to(float(plus_pos[0]), float(plus_pos[1]))
    minus.move_to(float(minus_pos[0]), float(minus_pos[1]))

    return VGroup(arrow, lbl, plus, minus)


def KirchhoffDemo(
    battery_emf: str = "V",
    r1_label: str = "R_1",
    r2_label: str = "R_2",
    current_label: str = "I",
    color_battery: str = GREEN,
    color_resistor: str = BLUE,
    color_current: str = YELLOW,
    battery_volts: float | None = None,
    r1_ohms: float | None = None,
    r2_ohms: float | None = None,
    show_voltage_drops: bool = False,
) -> VGroup:
    """Assemble a simple series R1-R2 loop with a battery and current arrow.

    Returns a VGroup centered at origin; shift/scale to place in scene.

    Physics mode. Pass all three of ``battery_volts``, ``r1_ohms``,
    ``r2_ohms`` (numeric) to auto-derive the circuit current via Ohm's
    law on the series total. When those are set, the current label
    defaults to ``I = X A`` (override by also passing ``current_label``).
    Set ``show_voltage_drops=True`` to render per-component voltage
    annotations (``+V`` across the battery, ``-I*R`` across each
    resistor) — the three numbers always sum to zero, which is the
    point of KVL.
    """
    from chalk.shapes import Arrow
    from chalk.tex import MathTex

    loop_w, loop_h = 5.0, 2.5
    hw, hh = loop_w / 2, loop_h / 2

    # Wire segments (corners of the rectangle)
    tl = (-hw,  hh)
    tr = ( hw,  hh)
    br = ( hw, -hh)
    bl = (-hw, -hh)

    battery  = Battery(bl, tl, polarity="right", color=color_battery)
    r1       = Resistor((-1.2, hh), (1.2, hh), color=color_resistor)
    r2       = Resistor((hw, 0.8), (hw, -0.8), color=color_resistor)
    top_wire = Wire(tl, tr, color=GREY, breaks=[r1])
    right_wire = Wire(tr, br, color=GREY, breaks=[r2])
    bottom_wire = Wire(br, bl, color=GREY)

    # Layout:
    #   - Component labels (R1, R2, V) sit INSIDE the loop with generous
    #     buffs so they never collide with resistor zigzag amplitude
    #     (~0.12 world) or battery plate half-width (~0.2).
    #   - Current arrow + label live OUTSIDE the loop, above the top wire.
    r1_lbl = MathTex(r1_label, color=color_resistor, scale=SCALE_LABEL)
    r1_lbl.move_to(0.0, hh - 0.85)            # 0.85 below R1 centerline
    r2_lbl = MathTex(r2_label, color=color_resistor, scale=SCALE_LABEL)
    r2_lbl.move_to(hw - 0.95, 0.0)            # 0.95 inside from R2 wire x

    batt_lbl = MathTex(battery_emf, color=color_battery, scale=SCALE_LABEL)
    batt_lbl.move_to(-hw + 0.95, 0.0)         # 0.95 inside from battery wire x

    # Current label: auto-fill with computed value when the numeric inputs
    # are given and the caller did not override ``current_label`` explicitly.
    _physics = (
        battery_volts is not None
        and r1_ohms is not None
        and r2_ohms is not None
        and (r1_ohms + r2_ohms) > 0
    )
    if _physics and current_label == "I":
        _i = battery_volts / (r1_ohms + r2_ohms)
        # Format 1.0 as "1", otherwise one decimal place.
        _i_str = f"{int(_i)}" if _i == int(_i) else f"{_i:.1f}"
        current_label = rf"I \;=\; {_i_str}\,\mathrm{{A}}"

    i_arrow = Arrow((-0.6, hh + 0.75), (0.6, hh + 0.75), color=color_current)
    i_lbl = MathTex(current_label, color=color_current, scale=SCALE_LABEL)
    i_lbl.move_to(0.0, hh + 1.05)

    extras: list = []
    if show_voltage_drops and _physics:
        _i = battery_volts / (r1_ohms + r2_ohms)

        def _fmt(v: float) -> str:
            # Signed, no trailing zeros unless needed.
            sign = "+" if v >= 0 else "-"
            mag = abs(v)
            mag_s = f"{int(mag)}" if mag == int(mag) else f"{mag:.1f}"
            return f"{sign}{mag_s}"

        v_batt_s = _fmt(battery_volts)
        v_r1_s = _fmt(-_i * r1_ohms)
        v_r2_s = _fmt(-_i * r2_ohms)

        # Voltage drops on the OUTSIDE of each component, clear of the
        # inside-the-loop resistance / EMF labels.
        v_batt_lbl = MathTex(
            rf"{v_batt_s}\,\mathrm{{V}}", color=color_battery, scale=SCALE_LABEL,
        )
        v_batt_lbl.move_to(-hw - 0.78, -0.75)     # below the battery label, outside

        v_r1_lbl = MathTex(
            rf"{v_r1_s}\,\mathrm{{V}}", color=color_resistor, scale=SCALE_LABEL,
        )
        v_r1_lbl.move_to(1.9, hh + 0.45)          # right-of-R1, above the top wire

        v_r2_lbl = MathTex(
            rf"{v_r2_s}\,\mathrm{{V}}", color=color_resistor, scale=SCALE_LABEL,
        )
        v_r2_lbl.move_to(hw + 0.78, -0.75)        # below R2, outside the loop

        extras.extend([v_batt_lbl, v_r1_lbl, v_r2_lbl])

    return VGroup(
        top_wire, right_wire, bottom_wire, battery, r1, r2,
        r1_lbl, r2_lbl, batt_lbl,
        i_arrow, i_lbl,
        *extras,
    )
