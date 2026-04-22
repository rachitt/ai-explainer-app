"""Tests for chalk.circuits: Resistor, Battery, Capacitor, Inductor, Switch,
Ground, Wire, CurrentFlow, VoltageLabel, KirchhoffDemo."""
from __future__ import annotations

import math
import numpy as np
import pytest

from chalk.circuits import (
    Resistor, Battery, Capacitor, Inductor, Switch, Ground,
    Wire, CurrentFlow, VoltageLabel, KirchhoffDemo,
)
from chalk.value_tracker import ValueTracker
from chalk.vgroup import VGroup
from chalk.redraw import AlwaysRedraw
from chalk.scene import Scene
from chalk.animation import FadeIn, ChangeValue
from chalk.camera import Camera2D


class _NullSink:
    def write(self, _): pass


def _attach(scene):
    cam = Camera2D()
    cam.pixel_width = 320
    cam.pixel_height = 180
    scene._attach(_NullSink(), camera=cam)


# ── Resistor ─────────────────────────────────────────────────────────────────

def test_resistor_is_vgroup():
    r = Resistor((0.0, 0.0), (3.0, 0.0))
    assert isinstance(r, VGroup)


def test_resistor_has_correct_segments():
    r = Resistor((0.0, 0.0), (4.0, 0.0), zigzag_count=4)
    # left connector + 2*4 teeth + right connector = 11 = 10 teeth + 2 connectors? ...
    # Actually: vertices = p0, anchor_L, 8 peaks, anchor_R, p1 → 12 vertices → 11 segments
    assert len(r.submobjects) == 11


def test_resistor_zero_length_safe():
    r = Resistor((1.0, 0.0), (1.0, 0.0))
    assert isinstance(r, VGroup)
    assert len(r.submobjects) == 0


def test_resistor_vertical():
    r = Resistor((0.0, 0.0), (0.0, 3.0), zigzag_count=3)
    assert len(r.submobjects) > 0


def test_resistor_renders():
    class RScene(Scene):
        def construct(self):
            r = Resistor((-2.0, 0.0), (2.0, 0.0))
            self.add(r)
            self.play(FadeIn(r, run_time=0.3))
            self.wait(0.2)
    scene = RScene()
    _attach(scene)
    scene.construct()


# ── Battery ──────────────────────────────────────────────────────────────────

def test_battery_is_vgroup():
    b = Battery((0.0, 0.0), (2.0, 0.0))
    assert isinstance(b, VGroup)


def test_battery_has_four_parts():
    b = Battery((0.0, 0.0), (2.0, 0.0))
    # wire_l, wire_r, neg_plate, pos_plate
    assert len(b.submobjects) == 4


def test_battery_polarity_left():
    b = Battery((0.0, 0.0), (2.0, 0.0), polarity="left")
    assert len(b.submobjects) == 4


# ── Capacitor ────────────────────────────────────────────────────────────────

def test_capacitor_is_vgroup():
    c = Capacitor((0.0, 0.0), (2.0, 0.0))
    assert isinstance(c, VGroup)


def test_capacitor_has_four_parts():
    c = Capacitor((0.0, 0.0), (2.0, 0.0))
    # wire_l, wire_r, plate1, plate2
    assert len(c.submobjects) == 4


# ── Inductor ─────────────────────────────────────────────────────────────────

def test_inductor_is_vgroup():
    ind = Inductor((0.0, 0.0), (3.0, 0.0), coils=3)
    assert isinstance(ind, VGroup)


def test_inductor_coil_count():
    ind = Inductor((0.0, 0.0), (3.0, 0.0), coils=4)
    # left connector + 4 arc coils + right connector = 6
    assert len(ind.submobjects) == 6


def test_inductor_renders():
    class IndScene(Scene):
        def construct(self):
            ind = Inductor((-2.0, 0.0), (2.0, 0.0), coils=3)
            self.add(ind)
            self.play(FadeIn(ind, run_time=0.3))
            self.wait(0.2)
    scene = IndScene()
    _attach(scene)
    scene.construct()


# ── Switch ───────────────────────────────────────────────────────────────────

def test_switch_open():
    s = Switch((0.0, 0.0), (2.0, 0.0), open=True)
    # wire_l, wire_r, dot_l, dot_r, lever
    assert len(s.submobjects) == 5


def test_switch_closed():
    s = Switch((0.0, 0.0), (2.0, 0.0), open=False)
    # wire_l, wire_r, dot_l, dot_r, bridge
    assert len(s.submobjects) == 5


# ── Ground ───────────────────────────────────────────────────────────────────

def test_ground_is_vgroup():
    g = Ground((0.0, 0.0))
    assert isinstance(g, VGroup)
    assert len(g.submobjects) == 3  # three horizontal lines


# ── Wire ─────────────────────────────────────────────────────────────────────

def test_wire_straight():
    w = Wire((0.0, 0.0), (3.0, 0.0))
    assert len(w.submobjects) == 1


def test_wire_three_segments():
    w = Wire((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0))
    assert len(w.submobjects) == 3


def test_wire_point_at_fraction_endpoints():
    w = Wire((0.0, 0.0), (4.0, 0.0))
    p0 = w.point_at_fraction(0.0)
    p1 = w.point_at_fraction(1.0)
    assert p0 == pytest.approx([0.0, 0.0], abs=1e-6)
    assert p1 == pytest.approx([4.0, 0.0], abs=1e-6)


def test_wire_point_at_fraction_midpoint():
    w = Wire((0.0, 0.0), (4.0, 0.0))
    mid = w.point_at_fraction(0.5)
    assert mid == pytest.approx([2.0, 0.0], abs=1e-6)


def test_wire_point_at_fraction_multi_segment():
    # L-shaped wire: right 2 units, then up 2 units (total 4 units)
    w = Wire((0.0, 0.0), (2.0, 0.0), (2.0, 2.0))
    # t=0.5 → exactly at the corner (2, 0)
    mid = w.point_at_fraction(0.5)
    assert mid == pytest.approx([2.0, 0.0], abs=1e-6)
    # t=0.75 → halfway up the vertical segment → (2, 1)
    q = w.point_at_fraction(0.75)
    assert q == pytest.approx([2.0, 1.0], abs=1e-6)


# ── CurrentFlow ──────────────────────────────────────────────────────────────

def test_current_flow_is_always_redraw():
    w = Wire((0.0, 0.0), (4.0, 0.0))
    cf = CurrentFlow(w, charge_count=5)
    assert isinstance(cf, AlwaysRedraw)


def test_current_flow_has_phase_tracker():
    w = Wire((0.0, 0.0), (4.0, 0.0))
    cf = CurrentFlow(w, charge_count=5)
    assert isinstance(cf.phase, ValueTracker)


def test_current_flow_dot_count():
    w = Wire((0.0, 0.0), (4.0, 0.0))
    cf = CurrentFlow(w, charge_count=6)
    cf.refresh()
    # AlwaysRedraw expands VGroup.submobjects directly → 6 Dot leaves
    assert len(cf.submobjects) == 6


def test_current_flow_renders():
    class CFScene(Scene):
        def construct(self):
            w = Wire((-3.0, 0.0), (3.0, 0.0))
            cf = CurrentFlow(w, charge_count=6)
            self.add(w)
            self.add(cf)
            self.play(FadeIn(w, run_time=0.2))
            self.play(ChangeValue(cf.phase, 1.0, run_time=0.5))
            self.wait(0.2)
    scene = CFScene()
    _attach(scene)
    scene.construct()


# ── VoltageLabel ─────────────────────────────────────────────────────────────

def test_voltage_label_is_vgroup():
    vl = VoltageLabel(across=((0.0, 0.0), (2.0, 0.0)), value="V")
    assert isinstance(vl, VGroup)


def test_voltage_label_has_parts():
    vl = VoltageLabel(across=((0.0, 0.0), (2.0, 0.0)), value="V")
    # arrow + label + plus + minus = 4 top-level items
    assert len(vl.submobjects) == 4


# ── KirchhoffDemo ─────────────────────────────────────────────────────────────

def test_kirchhoff_demo_is_vgroup():
    demo = KirchhoffDemo()
    assert isinstance(demo, VGroup)


def test_kirchhoff_demo_renders():
    class KDemo(Scene):
        def construct(self):
            demo = KirchhoffDemo()
            self.add(demo)
            self.play(FadeIn(demo, run_time=0.5))
            self.wait(0.3)
    scene = KDemo()
    _attach(scene)
    scene.construct()
