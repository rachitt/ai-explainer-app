import numpy as np
import pytest
from chalk._svg import parse_svg_to_vmobjects, _d_to_raw_cubic, _line_to_cubic


SIMPLE_SVG = """\
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10 10 L 90 10 L 90 90 L 10 90 Z"/>
</svg>
"""

CUBIC_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 0 50 C 0 20 100 20 100 50 Z"/>
</svg>
"""


def test_parse_simple_square():
    mobs = parse_svg_to_vmobjects(SIMPLE_SVG)
    assert len(mobs) >= 1
    assert mobs[0].points.shape[1] == 2
    assert len(mobs[0].points) % 4 == 0


def test_parse_cubic():
    mobs = parse_svg_to_vmobjects(CUBIC_SVG)
    assert len(mobs) >= 1
    # 1 cubic + closing line → 2 curves → 8 points
    assert mobs[0].points.shape == (8, 2)


def test_centered_at_origin():
    """parse_svg_to_vmobjects centers the result at origin."""
    mobs = parse_svg_to_vmobjects(SIMPLE_SVG)
    all_pts = np.vstack([m.points for m in mobs])
    cx = (all_pts[:, 0].min() + all_pts[:, 0].max()) / 2
    cy = (all_pts[:, 1].min() + all_pts[:, 1].max()) / 2
    assert abs(cx) < 0.01
    assert abs(cy) < 0.01


def test_raw_cubic_square_path():
    d = "M 10 10 L 90 10 L 90 90 L 10 90 Z"
    chains = list(_d_to_raw_cubic(d))
    assert len(chains) == 1
    assert len(chains[0]) % 4 == 0


def test_raw_cubic_open_path():
    d = "M 0 0 C 1 2 3 4 5 0"
    chains = list(_d_to_raw_cubic(d))
    assert len(chains) == 1
    assert chains[0].shape == (4, 2)


def test_line_to_cubic_collinear():
    p0 = np.array([0.0, 0.0])
    p1 = np.array([3.0, 0.0])
    c = _line_to_cubic(p0, p1)
    assert c.shape == (4, 2)
    np.testing.assert_allclose(c[0], p0)
    np.testing.assert_allclose(c[3], p1)
    np.testing.assert_allclose(c[1, 1], 0.0, atol=1e-10)
    np.testing.assert_allclose(c[2, 1], 0.0, atol=1e-10)


def test_vmobjects_have_correct_type():
    from chalk.mobject import VMobject
    mobs = parse_svg_to_vmobjects(SIMPLE_SVG)
    assert all(isinstance(m, VMobject) for m in mobs)
