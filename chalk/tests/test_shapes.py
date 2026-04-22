import math
import numpy as np
import pytest
from chalk.shapes import Circle, Square, Dot, Polygon, RegularPolygon, ArcBetweenPoints


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


# ── Dot ────────────────────────────────────────────────────────────────────

def test_dot_symmetric_bbox():
    pt = (1.5, -0.5)
    d = Dot(point=pt, radius=0.1)
    xs = d.points[:, 0]
    ys = d.points[:, 1]
    assert xs.min() == pytest.approx(pt[0] - 0.1, abs=0.01)
    assert xs.max() == pytest.approx(pt[0] + 0.1, abs=0.01)
    assert ys.min() == pytest.approx(pt[1] - 0.1, abs=0.01)
    assert ys.max() == pytest.approx(pt[1] + 0.1, abs=0.01)


def test_dot_default_point_is_origin():
    d = Dot()
    center = np.mean(d.points, axis=0)
    assert center == pytest.approx([0.0, 0.0], abs=0.01)


# ── Polygon ────────────────────────────────────────────────────────────────

def test_polygon_closes():
    p = Polygon((0, 0), (1, 0), (0.5, 1))
    first = p.points[0]
    last = p.points[-1]
    np.testing.assert_allclose(first, last, atol=1e-10)


def test_polygon_segment_count():
    # 4 vertices → 4 cubic Bezier segments → 16 control points
    # But last point of each segment overlaps first of next
    p = Polygon((0, 0), (1, 0), (1, 1), (0, 1))
    assert len(p.points) == 4 * 4  # 4 segments × 4 points


# ── RegularPolygon ─────────────────────────────────────────────────────────

def test_regular_hexagon_vertex_count():
    h = RegularPolygon(6, radius=1.0)
    # 6 segments × 4 points each
    assert len(h.points) == 6 * 4


def test_regular_hexagon_vertex_angles():
    h = RegularPolygon(6, radius=1.0, start_angle=0.0)
    # First vertex should be at (1, 0)
    first_vertex = h.points[0]
    assert first_vertex == pytest.approx([1.0, 0.0], abs=1e-9)


def test_regular_polygon_radius_matches():
    p = RegularPolygon(5, radius=2.0)
    # All corner vertices (every 4th point starting at 0) should be at radius 2
    for i in range(5):
        v = p.points[i * 4]
        assert np.linalg.norm(v) == pytest.approx(2.0, abs=1e-9)


# ── ArcBetweenPoints ───────────────────────────────────────────────────────

def test_arc_between_points_zero_angle_is_line():
    start = (0.0, 0.0)
    end = (4.0, 0.0)
    arc = ArcBetweenPoints(start, end, angle=0.0)
    # All points should be on the x-axis
    assert arc.points[:, 1] == pytest.approx(np.zeros(len(arc.points)), abs=1e-3)


def test_arc_between_points_semicircle_midpoint():
    start = (-1.0, 0.0)
    end = (1.0, 0.0)
    arc = ArcBetweenPoints(start, end, angle=math.pi)
    # Midpoint of arc should be near (0, 1) for positive angle (curves left/up)
    mid_idx = len(arc.points) // 2
    mid = arc.points[mid_idx]
    assert abs(mid[0]) < 0.3   # near x=0
    assert mid[1] > 0.5        # above y=0


def test_arc_first_and_last_points():
    start = (0.0, 0.0)
    end = (2.0, 0.0)
    arc = ArcBetweenPoints(start, end, angle=math.pi / 3)
    assert arc.points[0] == pytest.approx(list(start), abs=1e-6)
    assert arc.points[-1] == pytest.approx(list(end), abs=1e-6)
