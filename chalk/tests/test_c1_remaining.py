"""Tests for C1.6 remaining: ParametricFunction, camera pan/zoom, next_section, save_last_frame."""
from __future__ import annotations

import math
import os
import numpy as np
import pytest

from chalk.scene import Scene
from chalk.shapes import ParametricFunction, Circle
from chalk.animation import FadeIn, CameraShift, CameraZoom
from chalk.camera import Camera2D, CameraFrame


# ── Helpers ─────────────────────────────────────────────────────────────────

class _NullSink:
    def __init__(self):
        self.frame_count = 0
    def write(self, frame):
        self.frame_count += 1


def _attach(scene, sink=None):
    s = sink or _NullSink()
    cam = Camera2D()
    cam.pixel_width = 320
    cam.pixel_height = 180
    scene._attach(s, camera=cam)
    return s


# ── ParametricFunction ───────────────────────────────────────────────────────

def test_parametric_function_unit_circle():
    pf = ParametricFunction(
        lambda t: (math.cos(t), math.sin(t)),
        t_range=(0.0, 2 * math.pi, 0.1),
    )
    assert pf.points.shape[1] == 2
    assert len(pf.points) > 0
    # Points should lie near the unit circle
    xs = pf.points[:, 0]
    ys = pf.points[:, 1]
    radii = np.sqrt(xs**2 + ys**2)
    assert float(radii.max()) == pytest.approx(1.0, abs=0.02)


def test_parametric_function_line():
    pf = ParametricFunction(
        lambda t: (t, 2 * t),
        t_range=(0.0, 1.0, 0.1),
    )
    # First point at (0,0), last at (1,2)
    assert pf.points[0] == pytest.approx([0.0, 0.0], abs=1e-9)
    assert pf.points[-1] == pytest.approx([1.0, 2.0], abs=1e-9)


def test_parametric_function_renders():
    class PFScene(Scene):
        def construct(self):
            pf = ParametricFunction(
                lambda t: (t, math.sin(t)),
                t_range=(0.0, 2 * math.pi, 0.2),
                color="#58C4DD",
            )
            self.add(pf)
            self.play(FadeIn(pf, run_time=0.5))
            self.wait(0.3)

    sink = _NullSink()
    scene = PFScene()
    _attach(scene, sink)
    scene.construct()
    assert sink.frame_count > 0


def test_parametric_function_sample_count():
    pf = ParametricFunction(
        lambda t: (t, t),
        t_range=(0.0, 1.0, 0.1),
    )
    # t_range 0..1 step 0.1 → 11 samples → 10 segments → 40 points
    assert len(pf.points) == 40


# ── Camera pan / zoom ────────────────────────────────────────────────────────

def test_camera2d_default_no_pan_zoom():
    cam = Camera2D()
    assert cam.center_x == 0.0
    assert cam.center_y == 0.0
    assert cam.zoom == 1.0


def test_camera2d_world_to_pixel_no_pan():
    cam = Camera2D(frame_width=14.2, frame_height=8.0, pixel_width=142, pixel_height=80)
    pts = np.array([[0.0, 0.0]])
    px = cam.world_to_pixel(pts)
    assert px[0, 0] == pytest.approx(71.0, abs=0.5)
    assert px[0, 1] == pytest.approx(40.0, abs=0.5)


def test_camera2d_pan_shifts_pixel():
    cam = Camera2D(frame_width=14.2, frame_height=8.0, pixel_width=142, pixel_height=80)
    cam.center_x = 1.0  # pan right
    pts = np.array([[1.0, 0.0]])  # world origin + 1
    px = cam.world_to_pixel(pts)
    # (1 - 1) / 14.2 + 0.5 = 0.5 → pixel 71
    assert px[0, 0] == pytest.approx(71.0, abs=0.5)


def test_camera2d_zoom_scales():
    cam = Camera2D(frame_width=14.2, frame_height=8.0, pixel_width=142, pixel_height=80)
    cam.zoom = 2.0
    # A point at frame_width/4 from center should map to 3/4 of pixel_width
    pts = np.array([[14.2 / 4, 0.0]])
    px = cam.world_to_pixel(pts)
    # (14.2/4 * 2) / 14.2 + 0.5 = 0.5 + 0.5 = 1.0 → pixel 142
    assert px[0, 0] == pytest.approx(142.0, abs=1.0)


def test_camera_frame_proxy():
    cam = Camera2D()
    frame = CameraFrame(cam)
    frame.center_x = 3.0
    frame.center_y = -1.0
    frame.zoom = 2.0
    assert cam.center_x == 3.0
    assert cam.center_y == -1.0
    assert cam.zoom == 2.0


def test_camera_shift_animation():
    class ShiftScene(Scene):
        def construct(self):
            c = Circle(radius=0.5)
            self.add(c)
            self.play(FadeIn(c, run_time=0.3))
            self.play(CameraShift(self, dx=1.0, dy=0.5, run_time=0.3))

    sink = _NullSink()
    scene = ShiftScene()
    _attach(scene, sink)
    scene.construct()
    assert scene.camera.center_x == pytest.approx(1.0, abs=1e-6)
    assert scene.camera.center_y == pytest.approx(0.5, abs=1e-6)
    assert sink.frame_count > 0


def test_camera_zoom_animation():
    class ZoomScene(Scene):
        def construct(self):
            c = Circle(radius=0.5)
            self.add(c)
            self.play(FadeIn(c, run_time=0.3))
            self.play(CameraZoom(self, target_zoom=2.0, run_time=0.3))

    scene = ZoomScene()
    _attach(scene)
    scene.construct()
    assert scene.camera.zoom == pytest.approx(2.0, abs=1e-6)


# ── next_section ─────────────────────────────────────────────────────────────

def test_next_section_skip_writes_no_frames():
    """Beats before next_section(skip_animations=True) → 0 frames written."""
    class SkipScene(Scene):
        def construct(self):
            self.next_section("intro", skip_animations=True)
            c = Circle(radius=0.5)
            self.add(c)
            self.play(FadeIn(c, run_time=1.0))  # skipped
            self.wait(0.5)                       # skipped

    sink = _NullSink()
    scene = SkipScene()
    _attach(scene, sink)
    scene.construct()
    assert sink.frame_count == 0


def test_next_section_renders_after_flip():
    """Beats after next_section() (skip=False) are rendered normally."""
    class TwoSectionScene(Scene):
        def construct(self):
            self.next_section("intro", skip_animations=True)
            c = Circle(radius=0.5)
            self.add(c)
            self.play(FadeIn(c, run_time=0.5))  # skipped

            self.next_section("main")           # flip to render
            self.wait(0.5)                      # rendered

    sink = _NullSink()
    scene = TwoSectionScene()
    _attach(scene, sink)
    scene.construct()
    # 0.5s * 30fps = 15 frames from the wait
    assert sink.frame_count == pytest.approx(15, abs=2)


def test_next_section_records_bookmark():
    class BookmarkScene(Scene):
        def construct(self):
            self.next_section("alpha")
            self.wait(0.1)
            self.next_section("beta")

    scene = BookmarkScene()
    _attach(scene)
    scene.construct()
    names = [s[0] for s in scene.sections]
    assert "alpha" in names
    assert "beta" in names


def test_next_section_state_preserved_through_skip():
    """Mobs added+animated during a skipped section still exist afterward."""
    class StateScene(Scene):
        def construct(self):
            self.next_section("setup", skip_animations=True)
            c = Circle(radius=0.5)
            self.add(c)
            self.play(FadeIn(c, run_time=0.5))

            self.next_section("main")
            # c should still be in _mobjects
            assert c in self._mobjects

    scene = StateScene()
    _attach(scene)
    scene.construct()


# ── save_last_frame ──────────────────────────────────────────────────────────

def test_save_last_frame_writes_png(tmp_path):
    class SimpleScene(Scene):
        def construct(self):
            c = Circle(radius=0.5)
            self.add(c)
            self.play(FadeIn(c, run_time=0.3))
            self.save_last_frame(str(tmp_path / "frame.png"))

    scene = SimpleScene()
    _attach(scene)
    scene.construct()
    out = tmp_path / "frame.png"
    assert out.exists()
    assert out.stat().st_size > 0


def test_save_last_frame_valid_png(tmp_path):
    import png  # type: ignore[import]
    class BlueScene(Scene):
        def construct(self):
            from chalk.shapes import Rectangle
            r = Rectangle(width=3.0, height=2.0, color="#4FC3F7",
                          fill_color="#4FC3F7", fill_opacity=1.0)
            self.add(r)
            self.play(FadeIn(r, run_time=0.2))
            self.save_last_frame(str(tmp_path / "blue.png"))

    scene = BlueScene()
    cam = Camera2D()
    cam.pixel_width = 160
    cam.pixel_height = 90
    scene._attach(_NullSink(), camera=cam)
    scene.construct()
    reader = png.Reader(filename=str(tmp_path / "blue.png"))
    w, h, _, info = reader.read()
    assert w == 160
    assert h == 90
