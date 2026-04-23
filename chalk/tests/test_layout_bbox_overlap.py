"""Tests for actual bbox intersection checks."""
from __future__ import annotations

import shutil
import warnings

import pytest

from chalk import MathTex, Rectangle
from chalk.layout import (
    BboxOverlapError,
    BboxOverlapWarning,
    check_bbox_overlap,
)
from chalk.mobject import VMobject


def test_no_overlap_when_far_apart():
    left = Rectangle(width=1.0, height=1.0)
    right = Rectangle(width=1.0, height=1.0)
    left.shift(-3.0, 0.0)
    right.shift(3.0, 0.0)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = check_bbox_overlap([left, right])

    assert len(result) == 0
    assert caught == []


def test_overlap_when_centers_coincide():
    first = Rectangle(width=1.0, height=1.0)
    second = Rectangle(width=1.0, height=1.0)

    with pytest.warns(BboxOverlapWarning):
        result = check_bbox_overlap([first, second])

    assert len(result) == 1


def test_padding_flags_near_miss():
    left = Rectangle(width=1.0, height=1.0)
    right = Rectangle(width=1.0, height=1.0)
    left.shift(-0.6, 0.0)
    right.shift(0.6, 0.0)

    assert len(check_bbox_overlap([left, right], padding=0.0)) == 0
    with pytest.warns(BboxOverlapWarning):
        result = check_bbox_overlap([left, right], padding=0.15)

    assert len(result) == 1


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not installed")
def test_mathtex_overlap_caught():
    first = MathTex("x^2")
    second = MathTex("x^2")

    with pytest.warns(BboxOverlapWarning):
        result = check_bbox_overlap([first, second])

    assert len(result) == 1


def test_ignore_types_filter():
    first = Rectangle(width=1.0, height=1.0)
    second = Rectangle(width=1.0, height=1.0)

    result = check_bbox_overlap([first, second], ignore_types=(Rectangle,))

    assert len(result) == 0


def test_raise_on_fail():
    first = Rectangle(width=1.0, height=1.0)
    second = Rectangle(width=1.0, height=1.0)

    with pytest.raises(BboxOverlapError):
        check_bbox_overlap([first, second], raise_on_fail=True)
    with pytest.warns(BboxOverlapWarning):
        check_bbox_overlap([first, second], raise_on_fail=False)


def test_degenerate_mobjects_skipped():
    empty = VMobject()
    real = Rectangle(width=1.0, height=1.0)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = check_bbox_overlap([empty, real])

    assert len(result) == 0
    assert caught == []
