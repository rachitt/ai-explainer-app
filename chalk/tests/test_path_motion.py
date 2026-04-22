"""Tests for path_utils, MoveAlongPath, and Rotate."""
import math
import pytest
import numpy as np

from chalk.path_utils import arclength_point, sample_arclength
from chalk.shapes import Circle, Line
from chalk.mobject import VMobject
from chalk.animation import MoveAlongPath, Rotate, _iter_vmobjects
from chalk.vgroup import VGroup


def _make_horizontal_line(length: float = 10.0) -> VMobject:
    """Build a VMobject that is a straight horizontal line of given length."""
    from chalk.shapes import Line
    return Line((-length / 2, 0.0), (length / 2, 0.0), color="#FFFFFF")


def test_arclength_horizontal_line_midpoint():
    line = _make_horizontal_line(10.0)
    pt = arclength_point(line, 0.5)
    assert pt[0] == pytest.approx(0.0, abs=0.1)
    assert pt[1] == pytest.approx(0.0, abs=0.1)


def test_arclength_start_is_near_first_point():
    line = _make_horizontal_line(10.0)
    pt = arclength_point(line, 0.0)
    assert pt[0] == pytest.approx(-5.0, abs=0.1)


def test_arclength_end_is_near_last_point():
    line = _make_horizontal_line(10.0)
    pt = arclength_point(line, 1.0)
    assert pt[0] == pytest.approx(5.0, abs=0.1)


def test_move_along_path_places_mob_at_midpoint():
    from chalk.shapes import Circle as C
    dot = C(radius=0.08, color="#FFFFFF")
    dot.shift(0.0, 0.0)
    path_circle = Circle(radius=2.0)
    anim = MoveAlongPath(dot, path_circle, run_time=1.0)
    anim.begin()
    # alpha=0 → path start (rightmost point of circle, ~(2,0))
    anim.interpolate(0.0)
    center_0 = np.mean(dot.points, axis=0)
    # alpha=0.25 → quarter circle (~(0,2) for CCW circle)
    anim.interpolate(0.25)
    center_25 = np.mean(dot.points, axis=0)
    # Should have moved
    assert not np.allclose(center_0, center_25, atol=0.5)


def test_rotate_half_turn_flips_point():
    dot = Circle(radius=0.08, color="#FFFFFF")
    # Shift to (1, 0)
    dot.shift(1.0, 0.0)
    original_center = np.mean(dot.points, axis=0).copy()

    anim = Rotate(dot, math.pi, about_point=(0.0, 0.0), run_time=1.0)
    anim.begin()
    anim.finish()

    new_center = np.mean(dot.points, axis=0)
    assert new_center[0] == pytest.approx(-original_center[0], abs=1e-6)
    assert new_center[1] == pytest.approx(-original_center[1], abs=1e-6)


def test_rotate_full_turn_returns_to_start():
    dot = Circle(radius=0.08, color="#FFFFFF")
    dot.shift(2.0, 0.5)
    start_pts = dot.points.copy()

    anim = Rotate(dot, 2 * math.pi, about_point=(0.0, 0.0), run_time=1.0)
    anim.begin()
    anim.finish()

    assert np.allclose(dot.points, start_pts, atol=1e-9)


def test_rotate_preserves_vgroup_relative_positions():
    from chalk.shapes import Square
    a = Circle(radius=0.2, color="#FFFFFF")
    b = Square(side=0.3, color="#FFFFFF")
    a.shift(1.0, 0.0)
    b.shift(2.0, 0.0)
    grp = VGroup(a, b)

    # Record relative offset between centroids before rotation
    ca_before = np.mean(a.points, axis=0).copy()
    cb_before = np.mean(b.points, axis=0).copy()
    rel_before = cb_before - ca_before

    anim = Rotate(grp, math.pi / 2, about_point=(0.0, 0.0), run_time=1.0)
    anim.begin()
    anim.finish()

    ca_after = np.mean(a.points, axis=0)
    cb_after = np.mean(b.points, axis=0)
    rel_after = cb_after - ca_after

    assert np.linalg.norm(rel_before) == pytest.approx(np.linalg.norm(rel_after), abs=1e-6)
