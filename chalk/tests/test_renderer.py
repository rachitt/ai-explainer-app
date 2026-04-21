import numpy as np
import pytest
from chalk.camera import Camera2D
from chalk.renderer import CairoRenderer
from chalk.shapes import Circle


def make_renderer() -> CairoRenderer:
    r = CairoRenderer()
    r.begin_scene(Camera2D(pixel_width=320, pixel_height=240))
    return r


def test_frame_shape():
    r = make_renderer()
    frame = r.render_frame([])
    assert frame.shape == (240, 320, 4)
    assert frame.dtype == np.uint8


def test_background_color():
    cam = Camera2D(pixel_width=320, pixel_height=240, background_color="#ff0000")
    r = CairoRenderer()
    r.begin_scene(cam)
    frame = r.render_frame([])
    # Top-left corner should be red
    assert frame[0, 0, 0] > 200   # R high
    assert frame[0, 0, 1] < 10    # G low
    assert frame[0, 0, 2] < 10    # B low


def test_circle_renders_stroke():
    cam = Camera2D(pixel_width=320, pixel_height=240, background_color="#000000")
    r = CairoRenderer()
    r.begin_scene(cam)
    c = Circle(radius=1.0, color="#ffffff", stroke_width=4.0)
    frame = r.render_frame([c])
    # Frame should not be all black (circle pixels present)
    assert frame[:, :, 0].max() > 100


def test_camera_world_to_pixel_center():
    cam = Camera2D(pixel_width=320, pixel_height=240)
    origin = np.array([[0.0, 0.0]])
    px = cam.world_to_pixel(origin)
    np.testing.assert_allclose(px[0], [160.0, 120.0], atol=1.0)
