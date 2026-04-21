import numpy as np
import pytest
from chalk.mobject import VMobject, _lerp_hex, _hex_to_rgb, _rgb_to_hex


def _make_vmobj(n: int = 8) -> VMobject:
    m = VMobject(stroke_color="#ff0000", fill_color="#0000ff", fill_opacity=1.0)
    m.points = np.random.rand(n, 2)
    return m


def test_copy_independent():
    m = _make_vmobj(8)
    c = m.copy()
    c.points[0] = 999.0
    assert m.points[0, 0] != 999.0


def test_interpolate_alpha0():
    a = _make_vmobj(8)
    b = _make_vmobj(8)
    orig = a.points.copy()
    a.interpolate(b, 0.0)
    np.testing.assert_allclose(a.points, orig)


def test_interpolate_alpha1():
    a = _make_vmobj(8)
    b = _make_vmobj(8)
    target = b.points.copy()
    a.interpolate(b, 1.0)
    np.testing.assert_allclose(a.points, target)


def test_interpolate_midpoint():
    a = _make_vmobj(8)
    b = _make_vmobj(8)
    mid = (a.points + b.points) / 2
    a.interpolate(b, 0.5)
    np.testing.assert_allclose(a.points, mid)


def test_align_points_mismatch_raises():
    a = _make_vmobj(8)
    b = _make_vmobj(12)
    with pytest.raises(ValueError, match="point count mismatch"):
        a.align_points(b)


def test_lerp_hex_endpoints():
    assert _lerp_hex("#000000", "#ffffff", 0.0) == "#000000"
    assert _lerp_hex("#000000", "#ffffff", 1.0) == "#ffffff"
