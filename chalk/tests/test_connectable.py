"""Tests for Connectable shape endpoints."""
from __future__ import annotations

import math

import numpy as np
import pytest

from chalk.chemistry import Atom
from chalk.connectable import Connectable, circle_edge_toward, rect_edge_toward
from chalk.graph import Node
from chalk.physics import FreeBody, Mass, Spring


def test_circle_edge_toward_basic():
    assert circle_edge_toward(0.0, 0.0, 1.0, (2.0, 0.0)) == (1.0, 0.0)


def test_circle_edge_toward_diagonal():
    edge = circle_edge_toward(0.0, 0.0, 1.0, (1.0, 1.0))
    expected = math.sqrt(2) / 2
    assert edge == pytest.approx((expected, expected))


def test_rect_edge_toward_right():
    assert rect_edge_toward(0.0, 0.0, 1.0, 0.5, (2.0, 0.0)) == (1.0, 0.0)


def test_rect_edge_toward_top():
    assert rect_edge_toward(0.0, 0.0, 1.0, 0.5, (0.0, 2.0)) == (0.0, 0.5)


def test_rect_edge_toward_diagonal():
    assert rect_edge_toward(0.0, 0.0, 1.0, 0.5, (1.0, 1.0)) == (0.5, 0.5)


def test_node_is_connectable():
    assert isinstance(Node("A"), Connectable)


def test_atom_is_connectable():
    assert isinstance(Atom("C"), Connectable)


def test_mass_is_connectable():
    assert isinstance(Mass(), Connectable)


def test_spring_auto_shrinks_to_mass_edge():
    mass = Mass((0.0, 0.0), show_weight=False)
    spring = Spring(mass, (3.0, 0.0), coils=4)
    first_vertex = spring.submobjects[0].points[0]
    assert first_vertex[0] > 0.0
    assert first_vertex[0] < 1.0


def test_freebody_forces_start_at_edge():
    fb = FreeBody("m", [(1.5, 0.0, "F")])
    force_arrow = fb.submobjects[2]
    assert not np.allclose(force_arrow.points[0], (0.0, 0.0))
