"""Arc-length utilities for MoveAlongPath."""
from __future__ import annotations

import math
import numpy as np

from chalk.mobject import VMobject

_N_SAMPLES = 64  # points per cubic segment for arclength approximation


def _eval_cubic(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray,
                p3: np.ndarray, t: float) -> np.ndarray:
    u = 1.0 - t
    return u**3 * p0 + 3 * u**2 * t * p1 + 3 * u * t**2 * p2 + t**3 * p3


def sample_arclength(path: VMobject, n: int = _N_SAMPLES) -> tuple[np.ndarray, np.ndarray]:
    """Return (cumulative_arclength_normalized, points) sampled along path.

    Walks each cubic Bezier curve in path.points at `n` internal points,
    builds a chord-length polyline, and normalizes total length to [0, 1].
    """
    pts = path.points
    n_pts = len(pts)
    if n_pts < 4:
        return np.array([0.0, 1.0]), np.array([pts[0], pts[0]])

    sampled: list[np.ndarray] = []
    i = 0
    while i + 3 < n_pts:
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        for k in range(n + 1):
            t = k / n
            sampled.append(_eval_cubic(p0, p1, p2, p3, t))
        i += 4

    if not sampled:
        return np.array([0.0, 1.0]), np.stack([pts[0], pts[-1]])

    points_arr = np.stack(sampled)
    diffs = np.linalg.norm(np.diff(points_arr, axis=0), axis=1)
    cumlength = np.concatenate([[0.0], np.cumsum(diffs)])
    total = cumlength[-1]
    if total < 1e-12:
        cumlength_norm = np.linspace(0.0, 1.0, len(cumlength))
    else:
        cumlength_norm = cumlength / total
    return cumlength_norm, points_arr


def arclength_point(path: VMobject, t: float) -> np.ndarray:
    """Return (x, y) at normalized arclength t ∈ [0, 1] along path."""
    t = max(0.0, min(1.0, t))
    lengths, points = sample_arclength(path)
    idx = int(np.searchsorted(lengths, t, side="left"))
    idx = max(1, min(idx, len(lengths) - 1))
    t0, t1 = lengths[idx - 1], lengths[idx]
    dt = t1 - t0
    if dt < 1e-12:
        return points[idx]
    local = (t - t0) / dt
    return (1.0 - local) * points[idx - 1] + local * points[idx]
