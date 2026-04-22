"""Tests for Brace and brace_label."""
import pytest
import numpy as np

from chalk.brace import Brace
from chalk.layout import brace_label
from chalk.shapes import Rectangle


def test_brace_down_width_covers_target():
    rect = Rectangle(width=4.0, height=1.0)
    b = Brace(rect, direction="DOWN")
    xs = b.points[:, 0]
    # Brace should span at least the target's width
    assert float(xs.max() - xs.min()) >= 3.99


def test_brace_up_tip_above_target():
    rect = Rectangle(width=2.0, height=1.0)
    b = Brace(rect, direction="UP")
    tip = b.get_tip()
    # rect top is at y=0.5; tip should be above that
    assert tip[1] > 0.5


def test_brace_down_tip_below_target():
    rect = Rectangle(width=2.0, height=1.0)
    b = Brace(rect, direction="DOWN")
    tip = b.get_tip()
    # rect bottom is at y=-0.5; tip should be below that
    assert tip[1] < -0.5


def test_brace_tip_centered_horizontally():
    rect = Rectangle(width=4.0, height=1.0)
    b = Brace(rect, direction="DOWN")
    tip = b.get_tip()
    # Rect centered at origin; tip should be near x=0
    assert abs(tip[0]) < 0.1


def test_brace_label_positions_label_at_tip():
    rect = Rectangle(width=3.0, height=1.0)
    brace, lbl = brace_label(rect, r"L", direction="DOWN")
    tip = brace.get_tip()
    lbl_bb = lbl.bbox()
    lbl_cy = (lbl_bb[1] + lbl_bb[3]) / 2
    # Label center should be below the tip
    assert lbl_cy < tip[1]


def test_brace_left_tip_left_of_target():
    rect = Rectangle(width=2.0, height=2.0)
    b = Brace(rect, direction="LEFT")
    tip = b.get_tip()
    # rect left edge at x=-1.0; tip should be to the left
    assert tip[0] < -1.0
