"""Tests for Indicate, Flash, Circumscribe, and there_and_back."""
import math
import pytest
import numpy as np

from chalk.animation import Indicate, Flash, Circumscribe
from chalk.rate_funcs import there_and_back
from chalk.shapes import Circle, Rectangle


# ── there_and_back ─────────────────────────────────────────────────────────

def test_there_and_back_at_0():
    assert there_and_back(0.0) == pytest.approx(0.0)


def test_there_and_back_at_1():
    assert there_and_back(1.0) == pytest.approx(0.0)


def test_there_and_back_at_half():
    assert there_and_back(0.5) == pytest.approx(1.0)


# ── Indicate ───────────────────────────────────────────────────────────────

def test_indicate_at_alpha0_original_scale():
    mob = Circle(radius=1.0)
    orig_pts = mob.points.copy()
    anim = Indicate(mob, scale_factor=1.5)
    anim.begin()
    anim.interpolate(0.0)
    np.testing.assert_allclose(mob.points, orig_pts, atol=1e-9)


def test_indicate_at_alpha1_returns_original():
    mob = Circle(radius=1.0)
    orig_pts = mob.points.copy()
    orig_color = mob.fill_color
    anim = Indicate(mob, scale_factor=1.5, color="#FFD54F")
    anim.begin()
    anim.finish()
    np.testing.assert_allclose(mob.points, orig_pts, atol=1e-9)
    assert mob.fill_color == orig_color


def test_indicate_at_midpoint_scaled():
    mob = Circle(radius=1.0)
    anim = Indicate(mob, scale_factor=1.2, color="#FFD54F")
    anim.begin()
    anim.interpolate(0.5)
    # Radius should be ~1.2 at the midpoint (there_and_back(0.5)=1.0)
    xs = mob.points[:, 0]
    approx_radius = (xs.max() - xs.min()) / 2
    assert float(approx_radius) > 1.0  # scaled up


def test_indicate_at_midpoint_recolored():
    mob = Circle(radius=1.0, color="#FFFFFF")
    anim = Indicate(mob, scale_factor=1.2, color="#FFD54F")
    anim.begin()
    anim.interpolate(0.5)
    assert mob.fill_color == "#FFD54F"


# ── Flash ──────────────────────────────────────────────────────────────────

def test_flash_correct_line_count():
    anim = Flash((0.0, 0.0), num_lines=8)
    assert len(anim.mobjects) == 8


def test_flash_lines_radial():
    anim = Flash((0.0, 0.0), num_lines=12, line_length=0.3)
    # All lines should start near the origin
    for line in anim.mobjects:
        assert np.linalg.norm(line.points[0]) < 0.5


def test_flash_finish_invisible():
    anim = Flash((0.0, 0.0), num_lines=4)
    anim.begin()
    anim.finish()
    for line in anim.mobjects:
        assert line.stroke_opacity == pytest.approx(0.0)


# ── Circumscribe ────────────────────────────────────────────────────────────

def test_circumscribe_rect_bbox_covers_target():
    mob = Rectangle(width=3.0, height=1.5)
    anim = Circumscribe(mob, shape="rect", buff=0.1)
    anim.begin()
    outline = anim._outline
    assert outline is not None
    xs = outline.points[:, 0]
    ys = outline.points[:, 1]
    assert float(xs.max() - xs.min()) >= 3.0 + 2 * 0.1 - 0.01


def test_circumscribe_finish_visible():
    mob = Rectangle(width=2.0, height=1.0)
    anim = Circumscribe(mob, shape="rect")
    anim.begin()
    anim.finish()
    assert anim._outline is not None
    assert anim._outline.stroke_opacity == pytest.approx(1.0)
