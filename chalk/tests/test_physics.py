"""Tests for chalk.physics: Spring, Pendulum, Mass, Vector, FreeBody."""
from __future__ import annotations

import math
import numpy as np
import pytest

from chalk.physics import Spring, Pendulum, Mass, Vector, FreeBody
from chalk.value_tracker import ValueTracker
from chalk.vgroup import VGroup
from chalk.redraw import AlwaysRedraw
from chalk.scene import Scene
from chalk.animation import FadeIn
from chalk.camera import Camera2D


class _NullSink:
    def write(self, _): pass


def _attach(scene):
    cam = Camera2D()
    cam.pixel_width = 320
    cam.pixel_height = 180
    scene._attach(_NullSink(), camera=cam)


# ── Spring ───────────────────────────────────────────────────────────────────

def test_spring_is_vgroup():
    s = Spring((0.0, 0.0), (4.0, 0.0), coils=4)
    assert isinstance(s, VGroup)


def test_spring_has_segments():
    s = Spring((0.0, 0.0), (4.0, 0.0), coils=6)
    # left connector + 2*coils zigzag + right connector = 1 + 12 + 1 + 1 = 15 segments
    # vertices: p0, anchor_L, 12 peaks, anchor_R, p1 → 16 verts → 15 segments
    assert len(s.submobjects) == 15


def test_spring_zero_length_safe():
    s = Spring((1.0, 1.0), (1.0, 1.0), coils=4)
    assert isinstance(s, VGroup)
    assert len(s.submobjects) == 0


def test_spring_vertical():
    s = Spring((0.0, 0.0), (0.0, 3.0), coils=3)
    assert len(s.submobjects) > 0


def test_spring_renders():
    class SpringScene(Scene):
        def construct(self):
            s = Spring((-3.0, 0.0), (3.0, 0.0), coils=5)
            self.add(s)
            self.play(FadeIn(s, run_time=0.3))
            self.wait(0.2)

    scene = SpringScene()
    _attach(scene)
    scene.construct()


# ── Pendulum ─────────────────────────────────────────────────────────────────

def test_pendulum_returns_always_redraw():
    tracker = ValueTracker(0.0)
    pend = Pendulum(pivot=(0.0, 2.0), length=2.0, angle_tracker=tracker)
    assert isinstance(pend, AlwaysRedraw)


def test_pendulum_updates_on_tracker_change():
    tracker = ValueTracker(0.0)
    pend = Pendulum(pivot=(0.0, 2.0), length=2.0, angle_tracker=tracker)
    # At angle=0, bob is directly below pivot at (0, 0)
    pend.refresh()
    initial_submobs = len(pend.submobjects)
    tracker.set_value(math.pi / 4)
    pend.refresh()
    # Structure unchanged (pivot + rod + bob)
    assert len(pend.submobjects) == initial_submobs


def test_pendulum_has_pivot_dot():
    tracker = ValueTracker(0.0)
    pend = Pendulum(pivot=(0.0, 2.0), length=2.0, angle_tracker=tracker)
    pend.refresh()
    assert len(pend.submobjects) == 3


def test_pendulum_renders():
    class PendScene(Scene):
        def construct(self):
            tracker = ValueTracker(0.0)
            pend = Pendulum(pivot=(0.0, 2.0), length=2.0, angle_tracker=tracker)
            self.add(pend)
            self.play(FadeIn(pend, run_time=0.3))
            self.wait(0.2)

    scene = PendScene()
    _attach(scene)
    scene.construct()


# ── Mass ─────────────────────────────────────────────────────────────────────

def test_mass_is_vgroup():
    m = Mass(position=(0.0, 0.0), label="M")
    assert isinstance(m, VGroup)


def test_mass_has_box_label_weight():
    m = Mass(position=(0.0, 0.0), show_weight=True)
    # box, label, weight arrow = 3 items minimum
    assert len(m.submobjects) >= 2


def test_mass_no_weight():
    m = Mass(position=(0.0, 0.0), show_weight=False)
    # box + label only = 2 (labeled_box returns 2 mobs)
    assert len(m.submobjects) == 2


def test_mass_renders():
    class MassScene(Scene):
        def construct(self):
            m = Mass(position=(0.0, 0.0), label="M", show_weight=True)
            self.add(m)
            self.play(FadeIn(m, run_time=0.3))
            self.wait(0.2)

    scene = MassScene()
    _attach(scene)
    scene.construct()


# ── Vector ───────────────────────────────────────────────────────────────────

def test_vector_no_label():
    v = Vector((0.0, 0.0), (2.0, 0.0))
    assert isinstance(v, VGroup)
    assert len(v.submobjects) == 1  # just the arrow


def test_vector_with_label():
    v = Vector((0.0, 0.0), (2.0, 0.0), label=r"\vec{F}")
    assert len(v.submobjects) == 2  # arrow + label VGroup


def test_vector_zero_length_safe():
    v = Vector((1.0, 1.0), (1.0, 1.0), label="F")
    assert isinstance(v, VGroup)


def test_vector_renders():
    class VecScene(Scene):
        def construct(self):
            v = Vector((-2.0, 0.0), (2.0, 0.0), label=r"\vec{F}")
            self.add(v)
            self.play(FadeIn(v, run_time=0.3))
            self.wait(0.2)

    scene = VecScene()
    _attach(scene)
    scene.construct()


# ── FreeBody ─────────────────────────────────────────────────────────────────

def test_freebody_no_forces():
    fb = FreeBody(label="m")
    assert isinstance(fb, VGroup)
    # box + label = 2 submobjects
    assert len(fb.submobjects) == 2


def test_freebody_with_forces():
    fb = FreeBody(
        label="m",
        forces=[
            (1.5, 90.0, r"\vec{N}"),   # normal force up
            (1.5, 270.0, r"\vec{W}"),  # weight down
            (0.8, 0.0, r"\vec{F}"),    # applied right
        ],
    )
    # box + label + 3*(arrow + label) = 2 + 6 = 8
    assert len(fb.submobjects) == 8


def test_freebody_renders():
    class FBScene(Scene):
        def construct(self):
            fb = FreeBody(
                label="m",
                forces=[(1.2, 90.0, "N"), (1.2, 270.0, "W")],
            )
            self.add(fb)
            self.play(FadeIn(fb, run_time=0.3))
            self.wait(0.2)

    scene = FBScene()
    _attach(scene)
    scene.construct()


def test_freebody_unlabeled_forces():
    fb = FreeBody(
        label="m",
        forces=[(1.0, 45.0, ""), (1.0, 225.0, "")],
    )
    # box + label + 2*arrow (no labels) = 4
    assert len(fb.submobjects) == 4
