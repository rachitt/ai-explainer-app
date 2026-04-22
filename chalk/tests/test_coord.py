"""Tests for NumberLine and NumberPlane."""
import pytest
from chalk.coord import NumberLine, NumberPlane


def test_number_line_n2p_origin():
    nl = NumberLine(x_range=(-5.0, 5.0, 1.0), length=10.0)
    # x=0 should map to world (0, 0) when range is symmetric
    px, py = nl.n2p(0)
    assert px == pytest.approx(0.0, abs=1e-9)
    assert py == pytest.approx(0.0, abs=1e-9)


def test_number_line_n2p_end():
    nl = NumberLine(x_range=(-5.0, 5.0, 1.0), length=10.0)
    px, py = nl.n2p(5.0)
    assert px == pytest.approx(5.0, abs=1e-9)


def test_number_line_n2p_start():
    nl = NumberLine(x_range=(-5.0, 5.0, 1.0), length=10.0)
    px, py = nl.n2p(-5.0)
    assert px == pytest.approx(-5.0, abs=1e-9)


def test_number_line_n2p_midpoint():
    nl = NumberLine(x_range=(-5.0, 5.0, 1.0), length=10.0)
    px, py = nl.n2p(2.0)
    assert px == pytest.approx(2.0, abs=1e-9)


def test_number_line_p2n_roundtrip():
    nl = NumberLine(x_range=(-5.0, 5.0, 1.0), length=10.0)
    for v in [-5.0, -2.0, 0.0, 3.5, 5.0]:
        world = nl.n2p(v)
        back = nl.p2n(world)
        assert back == pytest.approx(v, abs=1e-9)


def test_number_plane_c2p_origin():
    np_ = NumberPlane(x_range=(-7.0, 7.0, 1.0), y_range=(-4.0, 4.0, 1.0))
    px, py = np_.c2p(0.0, 0.0)
    assert px == pytest.approx(0.0, abs=1e-9)
    assert py == pytest.approx(0.0, abs=1e-9)


def test_number_plane_c2p_corner():
    np_ = NumberPlane(x_range=(-7.0, 7.0, 1.0), y_range=(-4.0, 4.0, 1.0))
    px, py = np_.c2p(7.0, 4.0)
    assert px == pytest.approx(7.0, abs=1e-9)
    assert py == pytest.approx(4.0, abs=1e-9)


def test_number_plane_p2c_roundtrip():
    np_ = NumberPlane(x_range=(-7.0, 7.0, 1.0), y_range=(-4.0, 4.0, 1.0))
    for x, y in [(0, 0), (3.5, -2.0), (-7.0, 4.0)]:
        world = np_.c2p(x, y)
        back = np_.p2c(world)
        assert back[0] == pytest.approx(x, abs=1e-9)
        assert back[1] == pytest.approx(y, abs=1e-9)


def test_number_plane_grid_line_count():
    np_ = NumberPlane(x_range=(-3.0, 3.0, 1.0), y_range=(-2.0, 2.0, 1.0))
    # 7 vertical lines (−3 to 3 step 1) + 5 horizontal lines (−2 to 2 step 1) = 12
    # But NumberPlane stores all as Line VMobjects in submobjects
    from chalk.animation import _iter_vmobjects
    n = len(np_.submobjects)
    assert n == 7 + 5  # 7 vert + 5 horiz
