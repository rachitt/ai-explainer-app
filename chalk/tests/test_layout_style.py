import pytest
import numpy as np

from chalk import (
    Circle, Square, VGroup,
    next_to, place_in_zone,
    PRIMARY, YELLOW, BLUE, RED_FILL,
    SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT, SCALE_MIN,
    ZONE_TOP, ZONE_CENTER, ZONE_BOTTOM,
)


def test_palette_hex_format():
    for c in (PRIMARY, YELLOW, BLUE, RED_FILL):
        assert c.startswith("#") and len(c) == 7


def test_scale_tiers_descending_and_above_min():
    tiers = [SCALE_DISPLAY, SCALE_BODY, SCALE_LABEL, SCALE_ANNOT]
    assert tiers == sorted(tiers, reverse=True)
    assert all(t >= SCALE_MIN for t in tiers)


def test_zones_non_overlapping_and_span_safe_area():
    assert ZONE_TOP[0] == ZONE_CENTER[1]        # top meets center
    assert ZONE_CENTER[0] == ZONE_BOTTOM[1]     # center meets bottom
    assert ZONE_TOP[1] <= 3.5
    assert ZONE_BOTTOM[0] >= -3.5


def test_next_to_down_places_below_anchor():
    anchor = Square(side=1.0)
    anchor.shift(0.0, 2.0)  # centered at (0, 2)
    mob = Circle(radius=0.2)
    next_to(mob, anchor, direction="DOWN", buff=0.3)
    xmin, ymin, xmax, ymax = (
        mob.points[:, 0].min(), mob.points[:, 1].min(),
        mob.points[:, 0].max(), mob.points[:, 1].max(),
    )
    # Anchor bottom = 2.0 - 0.5 = 1.5; mob top should be 1.5 - 0.3 = 1.2
    assert abs(ymax - 1.2) < 1e-6


def test_next_to_right_places_to_right_of_anchor():
    anchor = Circle(radius=0.5)  # centered at origin
    mob = Circle(radius=0.3)
    next_to(mob, anchor, direction="RIGHT", buff=0.2)
    # Anchor right = 0.5; mob left should be 0.5 + 0.2 = 0.7
    assert abs(mob.points[:, 0].min() - 0.7) < 0.01


def test_next_to_works_with_vgroup():
    a = Circle(radius=0.3)
    b = Circle(radius=0.3)
    b.shift(1.0, 0.0)
    group = VGroup(a, b)
    label = Square(side=0.5)
    next_to(label, group, direction="UP", buff=0.4)
    # group top = 0.3; label bottom should be 0.3 + 0.4 = 0.7
    # (circle Bezier bbox extends slightly past radius due to handle length)
    assert abs(label.points[:, 1].min() - 0.7) < 0.01


def test_place_in_zone_centers_vertically_in_zone():
    mob = Circle(radius=0.2)
    place_in_zone(mob, ZONE_TOP, x=1.5)
    cx = (mob.points[:, 0].min() + mob.points[:, 0].max()) / 2
    cy = (mob.points[:, 1].min() + mob.points[:, 1].max()) / 2
    assert abs(cx - 1.5) < 1e-6
    assert abs(cy - (ZONE_TOP[0] + ZONE_TOP[1]) / 2) < 1e-6
