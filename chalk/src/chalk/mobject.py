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
        # Multi-subpath glyphs (e.g. letters with counters like D, 4).
        # When non-empty, renderer draws each subpath separately with evenodd fill rule.
        # self.points holds the concatenation for bbox/compat.
        self.subpaths: list[np.ndarray] = []
        self.fill_rule: str = "winding"  # "winding" or "evenodd"

    def copy(self) -> Self:
        new = object.__new__(type(self))
        new.points = self.points.copy()
        new.stroke_color = self.stroke_color
        new.stroke_width = self.stroke_width
        new.fill_color = self.fill_color
        new.fill_opacity = self.fill_opacity
        new.stroke_opacity = self.stroke_opacity
        new.subpaths = [s.copy() for s in self.subpaths]
        new.fill_rule = self.fill_rule
        return new  # type: ignore[return-value]

    def interpolate(self, other: "Mobject", alpha: float) -> None:
        if not isinstance(other, VMobject):
            raise TypeError("can only interpolate between VMobjects")
        self.align_points(other)
        if self.subpaths and other.subpaths:
            new_subs = [
                (1 - alpha) * a + alpha * b
                for a, b in zip(self.subpaths, other.subpaths)
            ]
            self.subpaths = new_subs
            self.points = np.concatenate(new_subs, axis=0)
        else:
            self.points = (1 - alpha) * self.points + alpha * other.points
        self.stroke_width = (1 - alpha) * self.stroke_width + alpha * other.stroke_width
        self.fill_opacity = (1 - alpha) * self.fill_opacity + alpha * other.fill_opacity
        self.stroke_opacity = (1 - alpha) * self.stroke_opacity + alpha * other.stroke_opacity
        self.stroke_color = _lerp_hex(self.stroke_color, other.stroke_color, alpha)
        self.fill_color = _lerp_hex(self.fill_color, other.fill_color, alpha)

    def shift(self, dx: float, dy: float) -> "VMobject":
        d = np.array([dx, dy])
        self.points = self.points + d
        self.subpaths = [s + d for s in self.subpaths]
        return self

    def scale(self, factor: float) -> "VMobject":
        self.points = self.points * factor
        self.subpaths = [s * factor for s in self.subpaths]
        return self

    def set_color(self, color: str) -> "VMobject":
        self.stroke_color = color
        return self

    def set_fill(self, color: str, opacity: float = 1.0) -> "VMobject":
        self.fill_color = color
        self.fill_opacity = opacity
        return self

    def align_points(self, other: "VMobject") -> None:
        """Ensure equal curve count via de Casteljau subdivision at t=0.5.

        When both sides have multi-subpath geometry (glyphs with counters,
        MathTex expressions composed of multiple glyphs per VMobject), align
        subpath-by-subpath: pad the shorter list with collapsed subpaths at the
        counterpart's centroid so extras morph from a point, then equalize
        curve count within each paired subpath.
        """
        if self.subpaths or other.subpaths:
            self_subs = self.subpaths if self.subpaths else [self.points]
            other_subs = other.subpaths if other.subpaths else [other.points]

            if len(self_subs) < len(other_subs):
                for extra in other_subs[len(self_subs):]:
                    self_subs.append(_collapsed_subpath(extra))
            elif len(other_subs) < len(self_subs):
                for extra in self_subs[len(other_subs):]:
                    other_subs.append(_collapsed_subpath(extra))

            for idx, (a, b) in enumerate(zip(self_subs, other_subs)):
                na = len(a) // self.POINTS_PER_CURVE
                nb = len(b) // self.POINTS_PER_CURVE
                if na == 0 or nb == 0:
                    continue
                if na < nb:
                    self_subs[idx] = _subdivide_to(a, nb)
                elif nb < na:
                    other_subs[idx] = _subdivide_to(b, na)

            self.subpaths = self_subs
            other.subpaths = other_subs
            self.points = np.concatenate(self_subs, axis=0)
            other.points = np.concatenate(other_subs, axis=0)
            return

        n1 = len(self.points) // self.POINTS_PER_CURVE
        n2 = len(other.points) // self.POINTS_PER_CURVE
        if n1 == n2:
            return
        if n1 < n2:
            self.points = _subdivide_to(self.points, n2)
        else:
            other.points = _subdivide_to(other.points, n1)


def _collapsed_subpath(ref: np.ndarray) -> np.ndarray:
    """Return a single-cubic subpath collapsed to ref's centroid.

    Used when aligning two VMobjects with unequal subpath counts: extras on
    one side are morphed to/from a point at the counterpart's center so they
    shrink to nothing rather than tearing across the frame.
    """
    if len(ref) == 0:
        center = np.zeros(2)
    else:
        center = ref.mean(axis=0)
    return np.tile(center, (VMobject.POINTS_PER_CURVE, 1))


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
