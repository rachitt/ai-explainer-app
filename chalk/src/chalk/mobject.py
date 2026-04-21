from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self
import numpy as np


class Mobject(ABC):
    """Abstract base for all mathematical objects in a chalk scene."""

    @abstractmethod
    def copy(self) -> Self: ...

    @abstractmethod
    def interpolate(self, other: "Mobject", alpha: float) -> None: ...


class VMobject(Mobject):
    """Vector mobject: defined by cubic Bezier control points with stroke/fill styling."""

    POINTS_PER_CURVE = 4

    def __init__(
        self,
        *,
        stroke_color: str = "#FFFFFF",
        stroke_width: float = 2.0,
        fill_color: str = "#000000",
        fill_opacity: float = 0.0,
        stroke_opacity: float = 1.0,
    ) -> None:
        self.points: np.ndarray = np.zeros((0, 2), dtype=float)
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.fill_color = fill_color
        self.fill_opacity = fill_opacity
        self.stroke_opacity = stroke_opacity

    def copy(self) -> Self:
        new = object.__new__(type(self))
        new.points = self.points.copy()
        new.stroke_color = self.stroke_color
        new.stroke_width = self.stroke_width
        new.fill_color = self.fill_color
        new.fill_opacity = self.fill_opacity
        new.stroke_opacity = self.stroke_opacity
        return new  # type: ignore[return-value]

    def interpolate(self, other: "Mobject", alpha: float) -> None:
        if not isinstance(other, VMobject):
            raise TypeError("can only interpolate between VMobjects")
        self.align_points(other)
        self.points = (1 - alpha) * self.points + alpha * other.points
        self.stroke_width = (1 - alpha) * self.stroke_width + alpha * other.stroke_width
        self.fill_opacity = (1 - alpha) * self.fill_opacity + alpha * other.fill_opacity
        self.stroke_opacity = (1 - alpha) * self.stroke_opacity + alpha * other.stroke_opacity
        self.stroke_color = _lerp_hex(self.stroke_color, other.stroke_color, alpha)
        self.fill_color = _lerp_hex(self.fill_color, other.fill_color, alpha)

    def align_points(self, other: "VMobject") -> None:
        """Ensure same point count. Day-1 stub: asserts equal; subdivision is week-2."""
        if len(self.points) != len(other.points):
            raise ValueError(
                f"point count mismatch: {len(self.points)} vs {len(other.points)}; "
                "align_points subdivision is week-2"
            )


def _hex_to_rgb(hex_color: str) -> np.ndarray:
    h = hex_color.lstrip("#")
    return np.array([int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)])


def _rgb_to_hex(rgb: np.ndarray) -> str:
    clamped = np.clip(rgb, 0.0, 1.0)
    return "#{:02x}{:02x}{:02x}".format(
        int(clamped[0] * 255), int(clamped[1] * 255), int(clamped[2] * 255)
    )


def _lerp_hex(a: str, b: str, alpha: float) -> str:
    return _rgb_to_hex((1 - alpha) * _hex_to_rgb(a) + alpha * _hex_to_rgb(b))
