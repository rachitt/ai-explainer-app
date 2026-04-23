import pytest

from chalk import SAFE_X, multi_panel


def test_multi_panel_three_evenly_spaced_fits_safe_x():
    gap = 0.4
    slots = multi_panel(3, gap=gap, x_extent=SAFE_X)

    assert len(slots) == 3
    for cx, cy, width, height in slots:
        assert cy == 0.0
        assert height == 3.0
        assert width >= 1.0
        assert cx - width / 2 >= SAFE_X[0]
        assert cx + width / 2 <= SAFE_X[1]

    for left, right in zip(slots, slots[1:]):
        left_edge = left[0] + left[2] / 2
        right_edge = right[0] - right[2] / 2
        assert right_edge - left_edge == pytest.approx(gap)


def test_multi_panel_custom_widths_scale_uniformly():
    slots = multi_panel(3, widths=[1.0, 2.0, 1.0], gap=0.5, x_extent=(-4.0, 4.0))

    widths = [slot[2] for slot in slots]
    assert widths == pytest.approx([1.75, 3.5, 1.75])
    assert sum(widths) + 2 * 0.5 == pytest.approx(8.0)


def test_multi_panel_one_panel():
    assert multi_panel(1, x_extent=(-2.0, 2.0)) == [(0.0, 0.0, 4.0, 3.0)]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n": 3, "gap": 1.0, "x_extent": (0.0, 2.5)},
        {"n": 3, "gap": 0.1, "x_extent": (0.0, 3.0)},
        {"n": 2, "widths": [1.0], "x_extent": (0.0, 4.0)},
    ],
)
def test_multi_panel_impossible_layouts_raise(kwargs):
    with pytest.raises(ValueError):
        multi_panel(**kwargs)
