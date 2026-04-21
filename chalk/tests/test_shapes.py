import numpy as np
import pytest
from chalk.shapes import Circle, Square


def test_circle_point_count():
    c = Circle(radius=1.0)
    assert c.points.shape == (64, 2)


def test_square_point_count():
    s = Square(side=2.0)
    assert s.points.shape == (64, 2)


def test_circle_closed():
    c = Circle(radius=1.0)
    np.testing.assert_allclose(c.points[0], c.points[-1], atol=1e-10)


def test_square_closed():
    s = Square(side=2.0)
    np.testing.assert_allclose(s.points[0], s.points[-1], atol=1e-10)


def test_circle_radius_scale():
    c1 = Circle(radius=1.0)
    c2 = Circle(radius=2.0)
    np.testing.assert_allclose(c2.points, c1.points * 2, atol=1e-10)


def test_transform_compatible():
    """Circle and Square have same point count for interpolation."""
    c = Circle()
    s = Square()
    assert c.points.shape == s.points.shape
