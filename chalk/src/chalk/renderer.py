"""Renderer protocol + CairoRenderer implementation.

Chalkboard aesthetic: when the ``CHALK_STYLE`` env var is set to
``chalkboard`` the renderer perturbs every stroke path with seeded
jitter and wobbles stroke width by a small fraction. This is chalk's
visual identity — hand-drawn chalk strokes on a slate board. Seed is
derived per-mobject so the same scene renders identically across runs
but different objects have different micro-wobble.
"""
from __future__ import annotations

import os
from typing import Protocol, Sequence
import numpy as np

from chalk.camera import Camera2D
from chalk.mobject import VMobject
from chalk.style import CHALK_JITTER_AMOUNT, CHALK_STROKE_WIDTH_JITTER


def _chalk_style_enabled() -> bool:
    return os.environ.get("CHALK_STYLE", "").lower() == "chalkboard"


def _jitter_points(pts_px: np.ndarray, seed: int, amount_px: float) -> np.ndarray:
    """Seeded per-point displacement in the perpendicular-ish direction.

    We use a dedicated numpy Generator so we don't perturb the caller's
    global RNG state. The same ``seed`` always produces the same jitter
    — required so a static object doesn't shimmer between frames.
    """
    rng = np.random.default_rng(seed)
    # Per-axis independent jitter is simpler than perpendicular and
    # reads the same at this magnitude. Kept small so curves still read.
    offsets = rng.normal(loc=0.0, scale=amount_px, size=pts_px.shape)
    return pts_px + offsets


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
        self._chalk_style = _chalk_style_enabled()

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

        subpaths = mob.subpaths if mob.subpaths else [mob.points]

        # Chalkboard: stable per-mobject seed so wobble does not shimmer
        # across frames for a static element. Glyphs (MathTex / Text)
        # opt out via `_no_chalk_jitter` — LaTeX letters lose readability
        # under even sub-pixel perturbation.
        chalk = self._chalk_style and not getattr(mob, "_no_chalk_jitter", False)
        mob_seed = (id(mob) & 0xFFFFFFFF) if chalk else 0
        amount_px = (
            camera.pixel_width / camera.frame_width * CHALK_JITTER_AMOUNT
            if chalk else 0.0
        )

        ctx.new_path()
        for sub_idx, subpath in enumerate(subpaths):
            pts_px = camera.world_to_pixel(subpath)
            if chalk and amount_px > 0.0:
                pts_px = _jitter_points(pts_px, seed=mob_seed + sub_idx, amount_px=amount_px)
            n = len(pts_px)
            if n < 4:
                continue
            ctx.move_to(float(pts_px[0, 0]), float(pts_px[0, 1]))
            i = 0
            while i + 3 < n:
                ctx.curve_to(
                    float(pts_px[i + 1, 0]), float(pts_px[i + 1, 1]),
                    float(pts_px[i + 2, 0]), float(pts_px[i + 2, 1]),
                    float(pts_px[i + 3, 0]), float(pts_px[i + 3, 1]),
                )
                i += 4
            if getattr(mob, "closed", True):
                ctx.close_path()

        fill_rule = (
            cairo.FILL_RULE_EVEN_ODD
            if mob.fill_rule == "evenodd"
            else cairo.FILL_RULE_WINDING
        )
        ctx.set_fill_rule(fill_rule)

        if mob.fill_opacity > 0:
            r, g, b, a = camera.hex_to_rgba(mob.fill_color, mob.fill_opacity)
            ctx.set_source_rgba(r, g, b, a)
            ctx.fill_preserve()

        r, g, b, a = camera.hex_to_rgba(mob.stroke_color, mob.stroke_opacity)
        ctx.set_source_rgba(r, g, b, a)
        # Chalk pressure wobble: small seeded width variation.
        stroke_w = mob.stroke_width
        if chalk:
            rng = np.random.default_rng(mob_seed ^ 0x5A5A5A5A)
            stroke_w = stroke_w * (1.0 + rng.uniform(-CHALK_STROKE_WIDTH_JITTER, CHALK_STROKE_WIDTH_JITTER))
        ctx.set_line_width(stroke_w)
        ctx.stroke()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
