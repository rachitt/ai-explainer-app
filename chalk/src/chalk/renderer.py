"""Renderer protocol + CairoRenderer implementation."""
from __future__ import annotations

from typing import Protocol, Sequence
import numpy as np

from chalk.camera import Camera2D
from chalk.mobject import VMobject


class Renderer(Protocol):
    def begin_scene(self, camera: Camera2D) -> None: ...
    def render_frame(self, mobjects: Sequence[VMobject]) -> np.ndarray:
        """Return RGBA frame as (H, W, 4) uint8 numpy array."""
        ...
    def end_scene(self) -> None: ...


class CairoRenderer:
    """Renders VMobjects to RGBA numpy arrays via pycairo."""

    def __init__(self) -> None:
        self._camera: Camera2D | None = None

    def begin_scene(self, camera: Camera2D) -> None:
        self._camera = camera

    def end_scene(self) -> None:
        pass

    def render_frame(self, mobjects: Sequence[VMobject]) -> np.ndarray:
        import cairo

        camera = self._camera
        assert camera is not None, "call begin_scene first"
        w, h = camera.pixel_width, camera.pixel_height

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        ctx = cairo.Context(surface)

        # Background
        r, g, b, a = camera.hex_to_rgba(camera.background_color)
        ctx.set_source_rgba(r, g, b, a)
        ctx.paint()

        for mob in mobjects:
            if not isinstance(mob, VMobject) or len(mob.points) < 4:
                continue
            self._draw_vmobject(ctx, camera, mob)

        # cairo uses ARGB32 (B, G, R, A in little-endian memory) — reorder to RGBA
        buf = surface.get_data()
        arr = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 4)
        # BGRA → RGBA
        rgba = arr[:, :, [2, 1, 0, 3]].copy()
        return rgba

    def _draw_vmobject(self, ctx: object, camera: Camera2D, mob: VMobject) -> None:
        import cairo

        pts_px = camera.world_to_pixel(mob.points)
        n = len(pts_px)

        ctx.new_path()
        ctx.move_to(float(pts_px[0, 0]), float(pts_px[0, 1]))

        i = 0
        while i + 3 < n:
            ctx.curve_to(
                float(pts_px[i + 1, 0]), float(pts_px[i + 1, 1]),
                float(pts_px[i + 2, 0]), float(pts_px[i + 2, 1]),
                float(pts_px[i + 3, 0]), float(pts_px[i + 3, 1]),
            )
            i += 4

        ctx.close_path()

        if mob.fill_opacity > 0:
            r, g, b, a = camera.hex_to_rgba(mob.fill_color, mob.fill_opacity)
            ctx.set_source_rgba(r, g, b, a)
            ctx.fill_preserve()

        r, g, b, a = camera.hex_to_rgba(mob.stroke_color, mob.stroke_opacity)
        ctx.set_source_rgba(r, g, b, a)
        ctx.set_line_width(mob.stroke_width)
        ctx.stroke()
