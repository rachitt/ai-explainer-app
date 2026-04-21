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
            m.points = m.points * factor
        return self

    def shift(self, delta_x: float, delta_y: float) -> "VGroup":
        import numpy as np
        d = np.array([delta_x, delta_y])
        for m in self.submobjects:
            m.points = m.points + d
        return self
