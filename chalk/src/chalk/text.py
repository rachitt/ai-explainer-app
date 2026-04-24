"""Text: plain (non-LaTeX) text primitive built on cairo toy font API.

Produces a VGroup of per-glyph VMobjects so Write/FadeIn/ShiftAnim stagger
naturally across characters. Use for captions, titles, UI labels — anywhere
MathTex's math-mode wrapping is wrong.
"""
from __future__ import annotations

import numpy as np

from chalk.mobject import VMobject
from chalk.vgroup import VGroup

# Cairo user-space unit → world unit. Tuned with _FONT_SIZE below so a scale=1.0
# Text renders at roughly SCALE_BODY height (~0.5 world units for caps).
_PT_TO_WORLD: float = 0.012
_FONT_SIZE: float = 48.0


def _line_to_cubic(p0: np.ndarray, p1: np.ndarray) -> np.ndarray:
    """Represent a straight line as a degenerate cubic Bezier."""
    return np.stack([p0, p0 + (p1 - p0) / 3.0, p0 + 2.0 * (p1 - p0) / 3.0, p1])


def _glyph_subpaths(
    ch: str,
    x_advance: float,
    font: str,
    weight: str,
    slant: str,
) -> list[np.ndarray]:
    """Extract cubic-Bezier subpaths for a single character via cairo text_path."""
    import cairo

    slant_map = {
        "normal": cairo.FONT_SLANT_NORMAL,
        "italic": cairo.FONT_SLANT_ITALIC,
        "oblique": cairo.FONT_SLANT_OBLIQUE,
    }
    weight_map = {
        "normal": cairo.FONT_WEIGHT_NORMAL,
        "bold": cairo.FONT_WEIGHT_BOLD,
    }

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    ctx = cairo.Context(surf)
    ctx.select_font_face(
        font,
        slant_map.get(slant, cairo.FONT_SLANT_NORMAL),
        weight_map.get(weight, cairo.FONT_WEIGHT_NORMAL),
    )
    ctx.set_font_size(_FONT_SIZE)
    ctx.move_to(x_advance, 0.0)
    ctx.text_path(ch)
    path = ctx.copy_path()

    subpaths: list[list[np.ndarray]] = []
    current: list[np.ndarray] = []
    subpath_start = np.zeros(2)
    cursor = np.zeros(2)

    for op, pts in path:
        if op == cairo.PATH_MOVE_TO:
            if current:
                subpaths.append(current)
                current = []
            subpath_start = np.array(pts, dtype=float)
            cursor = subpath_start.copy()
        elif op == cairo.PATH_LINE_TO:
            target = np.array(pts, dtype=float)
            current.append(_line_to_cubic(cursor, target))
            cursor = target
        elif op == cairo.PATH_CURVE_TO:
            p1 = np.array(pts[0:2], dtype=float)
            p2 = np.array(pts[2:4], dtype=float)
            p3 = np.array(pts[4:6], dtype=float)
            current.append(np.stack([cursor, p1, p2, p3]))
            cursor = p3
        elif op == cairo.PATH_CLOSE_PATH:
            if not np.allclose(cursor, subpath_start):
                current.append(_line_to_cubic(cursor, subpath_start))
            cursor = subpath_start.copy()

    if current:
        subpaths.append(current)

    return [np.concatenate(sp, axis=0) for sp in subpaths]


class Text(VGroup):
    """
    Plain text primitive rendered via cairo's toy font API.

    Each character becomes one VMobject so Write / staggered FadeIn reveal
    characters one at a time. For math, use MathTex instead.

    Args:
        string: text content (whitespace preserved for spacing)
        color: fill color (also used as stroke)
        stroke_width: outline width; 0 = fill only (default)
        fill_opacity: 0..1, defaults 1.0
        scale: uniform scale applied after layout
        font: cairo toy font family (e.g. "Sans", "Serif", "Monospace")
        weight: "normal" or "bold"
        slant: "normal", "italic", "oblique"
    """

    def __init__(
        self,
        string: str,
        color: str = "#FFFFFF",
        stroke_width: float = 0.0,
        fill_opacity: float = 1.0,
        scale: float = 1.0,
        font: str = "Sans",
        weight: str = "normal",
        slant: str = "normal",
    ) -> None:
        import cairo

        slant_map = {
            "normal": cairo.FONT_SLANT_NORMAL,
            "italic": cairo.FONT_SLANT_ITALIC,
            "oblique": cairo.FONT_SLANT_OBLIQUE,
        }
        weight_map = {
            "normal": cairo.FONT_WEIGHT_NORMAL,
            "bold": cairo.FONT_WEIGHT_BOLD,
        }

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        ctx = cairo.Context(surf)
        ctx.select_font_face(
            font,
            slant_map.get(slant, cairo.FONT_SLANT_NORMAL),
            weight_map.get(weight, cairo.FONT_WEIGHT_NORMAL),
        )
        ctx.set_font_size(_FONT_SIZE)

        mobs: list[VMobject] = []
        x_advance = 0.0
        glyph_arrays: list[list[np.ndarray]] = []
        glyph_widths: list[float] = []

        for ch in string:
            extents = ctx.text_extents(ch)
            if ch.isspace():
                glyph_arrays.append([])
                glyph_widths.append(extents.x_advance)
                x_advance += extents.x_advance
                continue
            subs = _glyph_subpaths(ch, x_advance, font, weight, slant)
            glyph_arrays.append(subs)
            glyph_widths.append(extents.x_advance)
            x_advance += extents.x_advance

        all_pts: list[np.ndarray] = []
        for subs in glyph_arrays:
            for s in subs:
                if len(s) > 0:
                    all_pts.append(s)

        if all_pts:
            stacked = np.vstack(all_pts)
            cx = (stacked[:, 0].min() + stacked[:, 0].max()) / 2
            cy = (stacked[:, 1].min() + stacked[:, 1].max()) / 2
        else:
            cx = cy = 0.0

        for subs in glyph_arrays:
            m = VMobject(
                stroke_color=color,
                stroke_width=stroke_width,
                fill_color=color,
                fill_opacity=fill_opacity,
                stroke_opacity=1.0 if stroke_width > 0 else 0.0,
            )
            world_subs: list[np.ndarray] = []
            for s in subs:
                centered = s - np.array([cx, cy])
                # y flip: cairo y grows down, world y grows up.
                scaled = np.stack(
                    [centered[:, 0] * _PT_TO_WORLD, -centered[:, 1] * _PT_TO_WORLD],
                    axis=1,
                )
                world_subs.append(scaled)
            if world_subs:
                m.points = np.concatenate(world_subs, axis=0)
                m.subpaths = world_subs
                m.fill_rule = "evenodd"
            # Glyphs skip chalkboard jitter — letter shapes need precision.
            m._no_chalk_jitter = True  # type: ignore[attr-defined]
            mobs.append(m)

        super().__init__(*mobs)
        self.string = string
        if scale != 1.0:
            self.scale(scale)
