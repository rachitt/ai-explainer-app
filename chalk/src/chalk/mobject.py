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

    def shift(self, dx: float, dy: float) -> "VMobject":
        self.points = self.points + np.array([dx, dy])
        return self

    def scale(self, factor: float) -> "VMobject":
        self.points = self.points * factor
        return self

    def set_color(self, color: str) -> "VMobject":
        self.stroke_color = color
        return self

    def set_fill(self, color: str, opacity: float = 1.0) -> "VMobject":
        self.fill_color = color
        self.fill_opacity = opacity
        return self

    def align_points(self, other: "VMobject") -> None:
        """Ensure equal curve count via de Casteljau subdivision at t=0.5."""
        n1 = len(self.points) // self.POINTS_PER_CURVE
        n2 = len(other.points) // self.POINTS_PER_CURVE
        if n1 == n2:
            return
        if n1 < n2:
            self.points = _subdivide_to(self.points, n2)
        else:
            other.points = _subdivide_to(other.points, n1)


def _split_cubic(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split cubic Bezier at t=0.5 via de Casteljau. p shape: (4, 2)."""
    m01 = (p[0] + p[1]) / 2
    m12 = (p[1] + p[2]) / 2
    m23 = (p[2] + p[3]) / 2
    m012 = (m01 + m12) / 2
    m123 = (m12 + m23) / 2
    center = (m012 + m123) / 2
    return (
        np.array([p[0], m01, m012, center]),
        np.array([center, m123, m23, p[3]]),
    )


def _subdivide_to(points: np.ndarray, target_n: int) -> np.ndarray:
    """Subdivide cubic Bezier chain to reach target_n curves."""
    ppc = 4
    curves = [points[i * ppc : (i + 1) * ppc] for i in range(len(points) // ppc)]
    while len(curves) < target_n:
        # Split the longest curve (by bounding box diagonal)
        lengths = [
            float(np.linalg.norm(c[-1] - c[0])) for c in curves
        ]
        idx = int(np.argmax(lengths))
        left, right = _split_cubic(curves[idx])
        curves = curves[:idx] + [left, right] + curves[idx + 1 :]
    return np.concatenate(curves, axis=0)


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
