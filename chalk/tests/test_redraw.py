"""Tests for always_redraw, AlwaysRedraw, and DecimalNumber."""
import pytest
from chalk.redraw import AlwaysRedraw, always_redraw, DecimalNumber
from chalk.shapes import Circle
from chalk.value_tracker import ValueTracker
from chalk.animation import _iter_vmobjects


def test_always_redraw_initial_refresh():
    rd = always_redraw(lambda: Circle(radius=0.5))
    leaves = _iter_vmobjects(rd)
    assert len(leaves) == 1


def test_always_redraw_refresh_regenerates():
    counter = [0]

    def factory():
        counter[0] += 1
        return Circle(radius=0.5)

    rd = AlwaysRedraw(factory)
    initial_count = counter[0]
    rd.refresh()
    assert counter[0] == initial_count + 1


def test_decimal_number_static_value():
    dn = DecimalNumber(3.14)
    assert dn._format_string() == "3.14"


def test_decimal_number_zero_places():
    dn = DecimalNumber(3.14, num_decimal_places=0)
    assert dn._format_string() == "3"


def test_decimal_number_unit():
    dn = DecimalNumber(5.0, unit=r"\,\mathrm{m}")
    assert r"\,\mathrm{m}" in dn._format_string()


def test_decimal_number_tracker():
    t = ValueTracker(2.5)
    dn = DecimalNumber(t, num_decimal_places=1)
    assert dn._format_string() == "2.5"
    t.set_value(7.3)
    assert dn._format_string() == "7.3"


def test_decimal_number_cache_not_rebuilt_if_same():
    t = ValueTracker(1.0)
    dn = DecimalNumber(t, num_decimal_places=2)
    # Trigger initial build
    first_cached = dn._cached_vgroup
    # Refresh with same value — cache should be reused
    dn.refresh()
    assert dn._cached_vgroup is first_cached


def test_decimal_number_rebuilds_on_value_change():
    t = ValueTracker(1.0)
    dn = DecimalNumber(t, num_decimal_places=2)
    first_cached = dn._cached_vgroup
    t.set_value(2.0)
    dn.refresh()
    assert dn._cached_vgroup is not first_cached


def test_scene_redrawable_driven_by_change_value():
    """After ChangeValue finishes, DecimalNumber reflects the new value."""
    from chalk.value_tracker import ValueTracker
    from chalk.animation import ChangeValue
    from chalk.rate_funcs import linear

    class NullSink:
        def write(self, frame): pass

    from chalk.scene import Scene
    from chalk.camera import Camera2D

    scene = Scene()
    scene._attach(NullSink())

    t = ValueTracker(0.0)
    dn = DecimalNumber(t, num_decimal_places=2)
    scene.add(dn)

    scene.play(ChangeValue(t, 10.0, run_time=0.1, rate_func=linear))
    # After playing, tracker is at 10.0
    assert t.get_value() == pytest.approx(10.0)
    # DecimalNumber should reflect this after next refresh
    dn.refresh()
    assert dn._last_string == "10.00"


def test_always_redraw_move_to_kwarg_applies_per_frame():
    from chalk.tex import MathTex
    from chalk.style import PRIMARY, SCALE_LABEL

    t = ValueTracker(0.0)
    readout = always_redraw(
        lambda: MathTex(rf"{t.get_value():.1f}", color=PRIMARY, scale=SCALE_LABEL),
        move_to=(3.0, -2.0),
    )

    cx, cy = _bbox_center(readout)
    assert abs(cx - 3.0) < 0.2 and abs(cy - (-2.0)) < 0.3

    t.set_value(9.9)
    readout.refresh()
    cx2, cy2 = _bbox_center(readout)
    assert abs(cx2 - 3.0) < 0.2 and abs(cy2 - (-2.0)) < 0.3


def test_always_redraw_shift_kwarg_applies_per_frame():
    from chalk.tex import MathTex
    from chalk.style import PRIMARY, SCALE_LABEL

    base = always_redraw(lambda: MathTex(r"3", color=PRIMARY, scale=SCALE_LABEL))
    shifted = always_redraw(
        lambda: MathTex(r"3", color=PRIMARY, scale=SCALE_LABEL),
        shift=(1.5, 0.0),
    )
    bx, by = _bbox_center(base)
    sx, sy = _bbox_center(shifted)
    assert abs(sx - (bx + 1.5)) < 0.1
    assert abs(sy - by) < 0.1


def _bbox_center(group) -> tuple[float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for m in _iter_vmobjects(group):
        pts = m.points
        if len(pts) == 0:
            continue
        xs.extend([float(pts[:, 0].min()), float(pts[:, 0].max())])
        ys.extend([float(pts[:, 1].min()), float(pts[:, 1].max())])
    return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
