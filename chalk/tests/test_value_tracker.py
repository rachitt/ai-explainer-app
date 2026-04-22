"""Tests for ValueTracker and ChangeValue animation."""
import pytest
from chalk.value_tracker import ValueTracker
from chalk.animation import ChangeValue
from chalk.rate_funcs import linear, smooth


def test_get_value_initial():
    t = ValueTracker(3.14)
    assert t.get_value() == pytest.approx(3.14)


def test_default_value_zero():
    t = ValueTracker()
    assert t.get_value() == pytest.approx(0.0)


def test_set_value():
    t = ValueTracker(0.0)
    t.set_value(5.0)
    assert t.get_value() == pytest.approx(5.0)


def test_set_value_returns_self():
    t = ValueTracker(0.0)
    result = t.set_value(7.0)
    assert result is t


def test_increment():
    t = ValueTracker(3.0)
    t.increment(2.0)
    assert t.get_value() == pytest.approx(5.0)


def test_increment_stacks():
    t = ValueTracker(0.0)
    t.increment(1.0)
    t.increment(2.0)
    t.increment(3.0)
    assert t.get_value() == pytest.approx(6.0)


def test_change_value_begin_snapshots_start():
    t = ValueTracker(7.0)
    anim = ChangeValue(t, 20.0)
    anim.begin()
    assert anim._start == pytest.approx(7.0)


def test_change_value_interpolate_midpoint_linear():
    t = ValueTracker(0.0)
    anim = ChangeValue(t, 10.0, rate_func=linear)
    anim.begin()
    anim.interpolate(0.5)
    assert t.get_value() == pytest.approx(5.0)


def test_change_value_finish_lands_on_target():
    t = ValueTracker(0.0)
    anim = ChangeValue(t, 42.0)
    anim.begin()
    anim.finish()
    assert t.get_value() == pytest.approx(42.0)


def test_change_value_mobjects_empty():
    t = ValueTracker(0.0)
    anim = ChangeValue(t, 1.0)
    assert anim.mobjects == []


def test_change_value_scene_level(tmp_path):
    """Playing ChangeValue in a Scene drives tracker to target value."""
    import io
    from chalk.scene import Scene
    from chalk.output import FFmpegSink

    class DemoScene(Scene):
        def construct(self):
            self.tracker = ValueTracker(0.0)
            self.play(ChangeValue(self.tracker, 10.0, run_time=1.0, rate_func=linear))

    scene = DemoScene()
    out = tmp_path / "out.mp4"

    class NullSink:
        def write(self, frame): pass

    scene._attach(NullSink())
    scene.construct()
    assert scene.tracker.get_value() == pytest.approx(10.0)
