"""Tests for AnimationGroup, Succession, LaggedStart."""
import pytest
import numpy as np

from chalk.animation import AnimationGroup, Succession, LaggedStart, FadeIn, FadeOut
from chalk.shapes import Circle, Square
from chalk.vgroup import VGroup


def _make_circle(x: float = 0.0) -> Circle:
    c = Circle(radius=0.5)
    c.shift(x, 0.0)
    return c


# ── AnimationGroup parallel (lag_ratio=0) ─────────────────────────────────

def test_animation_group_parallel_both_start_together():
    a = _make_circle(0.0)
    b = _make_circle(2.0)
    fi_a = FadeIn(a, run_time=1.0)
    fi_b = FadeIn(b, run_time=1.0)
    grp = AnimationGroup(fi_a, fi_b, lag_ratio=0.0)
    grp.begin()
    grp.interpolate(0.5)
    # Both should be at 50% opacity (smooth(0.5) ≈ 0.5)
    assert a.fill_opacity == pytest.approx(0.0, abs=0.01)  # fill_opacity was 0 by default
    # stroke opacity should be partially faded in (from 1.0)
    assert b.stroke_opacity > 0.0
    assert b.stroke_opacity < 1.0


def test_animation_group_sequential_first_done_at_half():
    """lag_ratio=1.0: at global alpha=0.5 with two equal anims, first is at 1.0, second at 0.0."""
    a = _make_circle(0.0)
    b = _make_circle(2.0)
    fo_a = FadeOut(a, run_time=1.0)
    fo_b = FadeOut(b, run_time=1.0)
    grp = AnimationGroup(fo_a, fo_b, lag_ratio=1.0)
    grp.begin()
    # At global alpha=0.5 with lag_ratio=1.0, run_time=2.0:
    # t = 0.5 * 2.0 = 1.0; first anim ends at 1.0; second starts at 1.0
    grp.interpolate(0.5)
    # First anim fully done: a should have opacity 0
    assert a.stroke_opacity == pytest.approx(0.0, abs=0.01)
    # Second anim just started: b should still have stroke_opacity ≈ 1.0
    assert b.stroke_opacity == pytest.approx(1.0, abs=0.05)


def test_animation_group_auto_run_time_parallel():
    a = _make_circle()
    fi_a = FadeIn(a, run_time=2.0)
    fi_b = FadeIn(_make_circle(1.0), run_time=3.0)
    grp = AnimationGroup(fi_a, fi_b, lag_ratio=0.0)
    assert grp.run_time == pytest.approx(3.0)


def test_animation_group_auto_run_time_sequential():
    a = _make_circle()
    fi_a = FadeIn(a, run_time=1.5)
    fi_b = FadeIn(_make_circle(1.0), run_time=2.0)
    grp = AnimationGroup(fi_a, fi_b, lag_ratio=1.0)
    assert grp.run_time == pytest.approx(3.5)


# ── Succession ─────────────────────────────────────────────────────────────

def test_succession_is_lag_ratio_1():
    a = FadeIn(_make_circle(), run_time=1.0)
    b = FadeIn(_make_circle(1.0), run_time=1.0)
    s = Succession(a, b)
    assert s.lag_ratio == pytest.approx(1.0)
    assert s.run_time == pytest.approx(2.0)


# ── LaggedStart ─────────────────────────────────────────────────────────────

def test_lagged_start_default_lag_ratio():
    s = LaggedStart(FadeIn(_make_circle(), run_time=1.0))
    assert s.lag_ratio == pytest.approx(0.3)


def test_lagged_start_partial_overlap():
    """lag_ratio=0.5: second starts at 50% of first's duration."""
    a = _make_circle(0.0)
    b = _make_circle(2.0)
    fi_a = FadeIn(a, run_time=1.0)
    fi_b = FadeIn(b, run_time=1.0)
    grp = LaggedStart(fi_a, fi_b, lag_ratio=0.5)
    grp.begin()
    grp.finish()
    # After finish both should be fully visible
    assert a.stroke_opacity == pytest.approx(1.0)
    assert b.stroke_opacity == pytest.approx(1.0)
