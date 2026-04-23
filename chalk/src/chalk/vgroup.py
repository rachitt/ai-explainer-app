"""VGroup: ordered container of VMobjects treated as a single scene element."""
from __future__ import annotations

from typing import Iterator
from chalk.mobject import VMobject


class VGroup:
    """Container of VMobjects. Scene.add/remove/render accept VGroup directly."""

    def __init__(self, *mobjects: VMobject) -> None:
        self.submobjects: list[VMobject] = list(mobjects)

    def add(self, *mobjects: VMobject) -> "VGroup":
        self.submobjects.extend(mobjects)
        return self

    def __iter__(self) -> Iterator[VMobject]:
        return iter(self.submobjects)

    def __len__(self) -> int:
        return len(self.submobjects)

    def set_color(self, color: str) -> "VGroup":
        for m in self.submobjects:
            m.stroke_color = color
        return self

    def set_fill(self, color: str, opacity: float = 1.0) -> "VGroup":
        for m in self.submobjects:
            m.fill_color = color
            m.fill_opacity = opacity
        return self

    def scale(self, factor: float) -> "VGroup":
        for m in self.submobjects:
            m.scale(factor)
        return self

    def shift(self, delta_x: float, delta_y: float) -> "VGroup":
        for m in self.submobjects:
            m.shift(delta_x, delta_y)
        return self

    def _iter_leaves(self) -> Iterator[VMobject]:
        """Recursively yield leaf VMobjects from nested VGroup/subclass tree.

        Needed because subclasses like MathTex, Text, and domain composites wrap
        their glyphs/children in nested VGroups. Leaf VMobjects have `.points`;
        VGroup instances do not.
        """
        for sub in self.submobjects:
            if isinstance(sub, VGroup):
                yield from sub._iter_leaves()
            else:
                yield sub

    def bbox(self) -> "tuple[float, float, float, float]":
        """Return (xmin, ymin, xmax, ymax) bounding box of all leaf VMobjects.

        Recurses through nested VGroup subclasses (MathTex, Text, composites).
        Prior implementation iterated `self.submobjects` one level deep and
        crashed with `AttributeError: '<subclass>' object has no attribute
        'points'` on any nested VGroup.
        """
        import numpy as np
        arrays = [m.points for m in self._iter_leaves() if len(m.points) > 0]
        if not arrays:
            return (0.0, 0.0, 0.0, 0.0)
        all_pts = np.vstack(arrays)
        return (float(all_pts[:, 0].min()), float(all_pts[:, 1].min()),
                float(all_pts[:, 0].max()), float(all_pts[:, 1].max()))

    @property
    def height(self) -> float:
        xmin, ymin, xmax, ymax = self.bbox()
        return ymax - ymin

    @property
    def width(self) -> float:
        xmin, ymin, xmax, ymax = self.bbox()
        return xmax - xmin

    def move_to(self, x: float, y: float) -> "VGroup":
        """Shift so bounding box center lands at (x, y)."""
        xmin, ymin, xmax, ymax = self.bbox()
        cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
        return self.shift(x - cx, y - cy)
