from __future__ import annotations

import math
from typing import Protocol, runtime_checkable

__all__ = [
    "Connectable",
    "resolve_endpoint",
    "get_center",
    "rect_edge_toward",
    "circle_edge_toward",
]


@runtime_checkable
class Connectable(Protocol):
    @property
    def center(self) -> tuple[float, float]: ...

    def edge_toward(self, target: tuple[float, float]) -> tuple[float, float]:
        """World point on this shape's boundary on the ray from center toward target."""
        ...


def resolve_endpoint(
    endpoint: Connectable | tuple[float, float],
    other_center: tuple[float, float],
) -> tuple[float, float]:
    """If endpoint is Connectable, call edge_toward(other_center). If tuple, return as-is."""
    if isinstance(endpoint, Connectable):
        return endpoint.edge_toward(other_center)
    return (float(endpoint[0]), float(endpoint[1]))


def get_center(endpoint: Connectable | tuple[float, float]) -> tuple[float, float]:
    if isinstance(endpoint, Connectable):
        return endpoint.center
    return (float(endpoint[0]), float(endpoint[1]))


def rect_edge_toward(
    center_x: float,
    center_y: float,
    half_w: float,
    half_h: float,
    target: tuple[float, float],
) -> tuple[float, float]:
    """Ray from rect center toward target, exit point on box boundary."""
    tx, ty = float(target[0]) - center_x, float(target[1]) - center_y
    if abs(tx) < 1e-9 and abs(ty) < 1e-9:
        return (center_x + half_w, center_y)
    t_x = half_w / abs(tx) if abs(tx) > 1e-9 else float("inf")
    t_y = half_h / abs(ty) if abs(ty) > 1e-9 else float("inf")
    t = min(t_x, t_y)
    return (center_x + t * tx, center_y + t * ty)


def circle_edge_toward(
    center_x: float,
    center_y: float,
    radius: float,
    target: tuple[float, float],
) -> tuple[float, float]:
    tx, ty = float(target[0]) - center_x, float(target[1]) - center_y
    d = math.hypot(tx, ty)
    if d < 1e-9:
        return (center_x + radius, center_y)
    return (center_x + radius * tx / d, center_y + radius * ty / d)
