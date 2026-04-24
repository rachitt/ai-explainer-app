import pytest

from chalk import (
    Axes,
    Circle,
    MathTex,
    Succession,
    Text,
    VMobject,
    Write,
    annotated_trace,
    animated_wait_with_pulse,
    build_up_sequence,
    highlight_and_hold,
    reveal_then_explain,
)


def test_reveal_then_explain_run_time():
    circle = Circle()
    label = Text("label")
    anim = reveal_then_explain(circle, label, run_time=2.0)
    assert abs(anim.run_time - 2.0) < 0.01


def test_highlight_and_hold_total_run_time():
    circle = Circle()
    anim = highlight_and_hold(circle, hold_seconds=1.5, indicate_run_time=0.8)
    assert isinstance(anim, Succession)
    assert abs(anim.run_time - 2.3) < 0.01


def test_annotated_trace_returns_animation_and_curve():
    ax = Axes(x_range=(0.0, 1.0), y_range=(0.0, 1.0), width=4.0, height=3.0)
    result = annotated_trace(
        ax,
        lambda x: x,
        x_start=0.0,
        x_end=1.0,
        annotations=[(0.5, Text("mid"))],
        run_time=2.4,
    )

    assert type(result) is tuple
    assert len(result) == 2
    assert isinstance(result[1], VMobject)
    assert hasattr(result[1], "points")
    assert abs(result[0].run_time - 2.4) < 0.01


def test_animated_wait_with_pulse_pulse_count():
    circle = Circle()
    anim = animated_wait_with_pulse(circle, pad_seconds=3.2, pulse_every=0.8)
    assert isinstance(anim, Succession)
    assert len(anim._animations) == 4
    assert abs(anim.run_time - 3.2) < 0.01


def test_build_up_sequence_timing():
    steps = [
        (Circle(),),
        (MathTex(r"x"), Write),
        (Text("done"),),
    ]
    anim = build_up_sequence(steps, step_run_time=1.0, inter_step_pause=0.3)
    assert isinstance(anim, Succession)
    assert abs(anim.run_time - 3.6) < 0.01
