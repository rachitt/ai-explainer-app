import numpy as np

from chalk import Text, Write, FadeIn
from chalk.vgroup import VGroup


def test_text_builds_per_glyph_vgroup():
    t = Text("Hi")
    assert isinstance(t, VGroup)
    # One VMobject per character (spaces produce empty VMobjects too).
    assert len(t.submobjects) == 2


def test_text_has_subpaths():
    t = Text("O")
    m = t.submobjects[0]
    # 'O' has an outer and inner contour → at least 2 subpaths.
    assert len(m.subpaths) >= 2


def test_text_space_produces_empty_vmobject():
    t = Text("A B")
    assert len(t.submobjects) == 3
    space = t.submobjects[1]
    assert len(space.points) == 0
    assert space.subpaths == []


def test_text_scale_applies():
    small = Text("X", scale=0.5)
    big = Text("X", scale=1.0)
    assert small.width < big.width


def test_write_alpha0_hides_all():
    t = Text("AB")
    fill0 = [m.fill_opacity for m in t.submobjects]
    w = Write(t, run_time=1.0, lag_ratio=0.5)
    w.begin()
    w.interpolate(0.0)
    for m in t.submobjects:
        assert m.fill_opacity == 0.0


def test_write_alpha1_restores():
    t = Text("AB")
    fill_targets = [m.fill_opacity for m in t.submobjects]
    w = Write(t, run_time=1.0, lag_ratio=0.5)
    w.begin()
    w.interpolate(1.0)
    for m, target in zip(t.submobjects, fill_targets):
        assert abs(m.fill_opacity - target) < 1e-9


def test_write_stagger_order():
    """At mid-alpha, earlier submobjects should be more revealed than later."""
    t = Text("ABCD")
    w = Write(t, run_time=1.0, lag_ratio=0.8)
    w.begin()
    w.interpolate(0.3)
    opacities = [m.fill_opacity for m in t.submobjects]
    # First glyph should be strictly ahead of the last at mid-alpha.
    assert opacities[0] > opacities[-1]


def test_write_single_vmobject_matches_fadein():
    from chalk.shapes import Circle
    c = Circle()
    c.fill_opacity = 0.7
    w = Write(c, run_time=1.0)
    w.begin()
    w.interpolate(0.5)
    # Single mobject → local alpha = global alpha (smooth eased).
    assert 0.0 < c.fill_opacity < 0.7


def test_write_lag_ratio_zero_simultaneous():
    t = Text("AB")
    w = Write(t, run_time=1.0, lag_ratio=0.0)
    w.begin()
    w.interpolate(0.5)
    a, b = (m.fill_opacity for m in t.submobjects)
    assert abs(a - b) < 1e-9
