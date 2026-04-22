"""Tests for chalk.layout overlap checks."""
from __future__ import annotations

import warnings

import numpy as np
import pytest

from chalk.layout import (
    LayoutOverlapError,
    LayoutOverlapWarning,
    check_no_overlap,
)


class _Mob:
    def __init__(self, position: tuple[float, float]) -> None:
        self.position = np.array(position, dtype=float)


def test_check_no_overlap_no_warn_when_separate():
    mobs = [_Mob((0.0, 0.0)), _Mob((2.0, 0.0))]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_no_overlap(mobs, min_sep=1.0)
    assert caught == []


def test_check_no_overlap_warns_when_close():
    mobs = [_Mob((0.0, 0.0)), _Mob((0.3, 0.0))]
    with pytest.warns(LayoutOverlapWarning):
        check_no_overlap(mobs, min_sep=1.0)


def test_check_no_overlap_raises_when_flagged():
    mobs = [_Mob((0.0, 0.0)), _Mob((0.3, 0.0))]
    with pytest.raises(LayoutOverlapError):
        check_no_overlap(mobs, min_sep=1.0, raise_on_fail=True)


def test_check_no_overlap_returns_pairs():
    mobs = [_Mob((0.0, 0.0)), _Mob((0.3, 0.0)), _Mob((2.0, 0.0))]
    with pytest.warns(LayoutOverlapWarning):
        overlaps = check_no_overlap(mobs, min_sep=1.0)
    assert overlaps == [(0, 1, pytest.approx(0.3))]
