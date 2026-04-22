"""Tests for Wire(breaks=[...]) component-terminal gaps."""
from __future__ import annotations

import numpy as np
import pytest

from chalk.circuits import Battery, Capacitor, Inductor, Resistor, Switch, Wire


def _segments(wire: Wire) -> list[tuple[np.ndarray, np.ndarray]]:
    return wire.segments


def test_series_components_expose_terminal_points():
    components = [
        Resistor((0.0, 0.0), (1.0, 0.0)),
        Battery((0.0, 0.0), (1.0, 0.0)),
        Capacitor((0.0, 0.0), (1.0, 0.0)),
        Inductor((0.0, 0.0), (1.0, 0.0)),
        Switch((0.0, 0.0), (1.0, 0.0)),
    ]

    for comp in components:
        assert comp.start == pytest.approx([0.0, 0.0], abs=1e-6)
        assert comp.end == pytest.approx([1.0, 0.0], abs=1e-6)


def test_wire_break_single_horizontal_component():
    r = Resistor((4.0, 0.0), (6.0, 0.0))
    wire = Wire((0.0, 0.0), (10.0, 0.0), breaks=[r])

    assert len(wire.submobjects) == 2
    assert _segments(wire)[0][0] == pytest.approx([0.0, 0.0], abs=1e-6)
    assert _segments(wire)[0][1] == pytest.approx([4.0, 0.0], abs=1e-6)
    assert _segments(wire)[1][0] == pytest.approx([6.0, 0.0], abs=1e-6)
    assert _segments(wire)[1][1] == pytest.approx([10.0, 0.0], abs=1e-6)


def test_wire_break_vertical_component():
    b = Battery((0.0, 2.0), (0.0, 4.0))
    wire = Wire((0.0, 0.0), (0.0, 6.0), breaks=[b])

    assert len(wire.submobjects) == 2
    assert _segments(wire)[0][1] == pytest.approx([0.0, 2.0], abs=1e-6)
    assert _segments(wire)[1][0] == pytest.approx([0.0, 4.0], abs=1e-6)


def test_wire_break_reversed_component_endpoints():
    r = Resistor((6.0, 0.0), (4.0, 0.0))
    wire = Wire((0.0, 0.0), (10.0, 0.0), breaks=[r])

    assert len(wire.submobjects) == 2
    assert _segments(wire)[0][1] == pytest.approx([4.0, 0.0], abs=1e-6)
    assert _segments(wire)[1][0] == pytest.approx([6.0, 0.0], abs=1e-6)


def test_wire_two_breaks_on_one_segment():
    r1 = Resistor((2.0, 0.0), (3.0, 0.0))
    r2 = Resistor((6.0, 0.0), (8.0, 0.0))
    wire = Wire((0.0, 0.0), (10.0, 0.0), breaks=[r1, r2])

    assert len(wire.submobjects) == 3
    assert _segments(wire)[0][0] == pytest.approx([0.0, 0.0], abs=1e-6)
    assert _segments(wire)[0][1] == pytest.approx([2.0, 0.0], abs=1e-6)
    assert _segments(wire)[1][0] == pytest.approx([3.0, 0.0], abs=1e-6)
    assert _segments(wire)[1][1] == pytest.approx([6.0, 0.0], abs=1e-6)
    assert _segments(wire)[2][0] == pytest.approx([8.0, 0.0], abs=1e-6)
    assert _segments(wire)[2][1] == pytest.approx([10.0, 0.0], abs=1e-6)


def test_wire_break_not_on_wire_raises_value_error():
    r = Resistor((4.0, 1.0), (6.0, 1.0))

    with pytest.raises(ValueError, match="do not lie on any wire segment"):
        Wire((0.0, 0.0), (10.0, 0.0), breaks=[r])


def test_wire_point_at_fraction_respects_broken_wire():
    r = Resistor((4.0, 0.0), (6.0, 0.0))
    wire = Wire((0.0, 0.0), (10.0, 0.0), breaks=[r])

    assert wire.point_at_fraction(0.0) == pytest.approx([0.0, 0.0], abs=1e-6)
    assert wire.point_at_fraction(0.5) == pytest.approx([4.0, 0.0], abs=1e-6)
    assert wire.point_at_fraction(1.0) == pytest.approx([10.0, 0.0], abs=1e-6)
