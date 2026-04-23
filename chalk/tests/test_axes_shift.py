import pytest

from chalk import Axes, BLUE, YELLOW, plot_function


def _bbox(mob):
    return (
        float(mob.points[:, 0].min()),
        float(mob.points[:, 1].min()),
        float(mob.points[:, 0].max()),
        float(mob.points[:, 1].max()),
    )


def test_to_point_tracks_axes_shift():
    ax = Axes(x_range=(0.0, 1.0), y_range=(0.0, 1.0), width=4.0, height=3.0)

    assert ax.to_point(0.0, 0.0) == pytest.approx((-2.0, -1.5))

    returned = ax.shift(2.5, 2.0)

    assert returned is ax
    assert ax.to_point(0.0, 0.0) == pytest.approx((0.5, 0.5))


def test_shifted_axes_plot_function_curves_do_not_overlap():
    left = Axes(x_range=(0.0, 1.0), y_range=(0.0, 1.0), width=4.0, height=3.0)
    right = Axes(x_range=(0.0, 1.0), y_range=(0.0, 1.0), width=4.0, height=3.0)
    left.shift(-4.4, 0.0)
    right.shift(4.4, 0.0)

    left_curve = plot_function(left, lambda x: x, color=BLUE)
    right_curve = plot_function(right, lambda x: x, color=YELLOW)

    left_bbox = _bbox(left_curve)
    right_bbox = _bbox(right_curve)
    assert left_bbox[2] < right_bbox[0]


def test_composed_shifts_accumulate_for_to_point():
    width = 4.0
    height = 3.0
    ax = Axes(x_range=(0.0, 1.0), y_range=(0.0, 1.0), width=width, height=height)

    ax.shift(1.0, 0.0)
    ax.shift(0.0, 2.0)

    assert ax.to_point(0.0, 0.0) == pytest.approx((1.0 - width / 2, 2.0 - height / 2))
