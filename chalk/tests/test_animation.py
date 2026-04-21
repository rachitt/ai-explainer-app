import numpy as np
import pytest
from chalk.shapes import Circle, Square
from chalk.animation import Transform


def test_transform_begin_caches():
    c = Circle()
    s = Square()
    t = Transform(c, s)
    original = c.points.copy()
    t.begin()
    np.testing.assert_allclose(t._start_points, original)


def test_transform_alpha0_unchanged():
    c = Circle()
    s = Square()
    start_pts = c.points.copy()
    t = Transform(c, s)
    t.begin()
    t.interpolate(0.0)
    np.testing.assert_allclose(c.points, start_pts, atol=1e-9)


def test_transform_alpha1_equals_target():
    c = Circle()
    s = Square()
    target_pts = s.points.copy()
    t = Transform(c, s)
    t.begin()
    t.interpolate(1.0)
    # With smooth rate func, alpha=1 → eased=1
    np.testing.assert_allclose(c.points, target_pts, atol=1e-9)


def test_transform_alpha05_midpoint():
    from chalk.rate_funcs import linear
    c = Circle()
    s = Square()
    start_pts = c.points.copy()
    target_pts = s.points.copy()
    mid = (start_pts + target_pts) / 2
    t = Transform(c, s, rate_func=linear)
    t.begin()
    t.interpolate(0.5)
    np.testing.assert_allclose(c.points, mid, atol=1e-9)


def test_transform_finish_leaves_target():
    c = Circle()
    s = Square()
    target_pts = s.points.copy()
    t = Transform(c, s)
    t.begin()
    t.finish()
    np.testing.assert_allclose(c.points, target_pts, atol=1e-9)


def test_transform_different_point_counts():
    """Transform should work when shapes have different initial curve counts."""
    from chalk.mobject import VMobject
    a = VMobject(stroke_color="#ff0000")
    a.points = np.zeros((4, 2))   # 1 curve
    b = VMobject(stroke_color="#0000ff")
    b.points = np.zeros((8, 2))   # 2 curves
    t = Transform(a, b)
    t.begin()
    t.interpolate(0.5)  # must not raise


def test_transform_color_lerp():
    from chalk.rate_funcs import linear
    c = Circle(color="#000000")
    s = Square(color="#ffffff")
    t = Transform(c, s, rate_func=linear)
    t.begin()
    t.interpolate(0.5)
    # Midpoint color should be grey
    r = int(c.stroke_color.lstrip("#")[0:2], 16)
    assert 120 < r < 136
