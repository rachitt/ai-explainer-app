"""Animation protocol and Transform implementation."""
from __future__ import annotations

from typing import Callable, Protocol, Sequence, Union
import numpy as np

from chalk.mobject import VMobject
from chalk.rate_funcs import smooth
from chalk.vgroup import VGroup


def _iter_vmobjects(target: Union[VMobject, VGroup]) -> list[VMobject]:
    """Flatten a VMobject/VGroup tree into a list of leaf VMobjects."""
    if isinstance(target, VGroup):
        out: list[VMobject] = []
        for child in target.submobjects:
            out.extend(_iter_vmobjects(child))
        return out
    return [target]


def _stagger_units(target: Union[VMobject, VGroup]) -> list[list[VMobject]]:
    """Group a target into stagger units for Write/sequential reveals.

    VMobject → one unit of one leaf. VGroup → one unit per top-level child,
    each flattened to its own leaves. Nested VGroups (e.g. a VGroup of MathTex
    objects) thus reveal child-by-child with all glyphs of one child appearing
    as a single unit.
    """
    if isinstance(target, VGroup):
        return [_iter_vmobjects(child) for child in target.submobjects]
    return [[target]]


class Animation(Protocol):
    run_time: float

    def begin(self) -> None: ...
    def interpolate(self, alpha: float) -> None: ...
    def finish(self) -> None: ...

    @property
    def mobjects(self) -> Sequence[VMobject]: ...


class Transform:
    """Morphs source VMobject into target VMobject over run_time seconds."""

    def __init__(
        self,
        source: VMobject,
        target: VMobject,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self.source = source
        self.target = target
        self.run_time = run_time
        self.rate_func = rate_func
        self._start_points: np.ndarray | None = None
        self._start_subpaths: list[np.ndarray] | None = None
        self._start_stroke_color: str = source.stroke_color
        self._start_fill_color: str = source.fill_color
        self._start_stroke_width: float = source.stroke_width
        self._start_fill_opacity: float = source.fill_opacity
        self._start_stroke_opacity: float = source.stroke_opacity

    @property
    def mobjects(self) -> list[VMobject]:
        return [self.source]

    def begin(self) -> None:
        self._start_points = self.source.points.copy()
        self._start_subpaths = [s.copy() for s in self.source.subpaths]
        self._start_stroke_color = self.source.stroke_color
        self._start_fill_color = self.source.fill_color
        self._start_stroke_width = self.source.stroke_width
        self._start_fill_opacity = self.source.fill_opacity
        self._start_stroke_opacity = self.source.stroke_opacity

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        assert self._start_points is not None
        assert self._start_subpaths is not None
        # Restore to start state, then let VMobject.interpolate do the lerp
        self.source.points = self._start_points.copy()
        self.source.subpaths = [s.copy() for s in self._start_subpaths]
        self.source.stroke_color = self._start_stroke_color
        self.source.fill_color = self._start_fill_color
        self.source.stroke_width = self._start_stroke_width
        self.source.fill_opacity = self._start_fill_opacity
        self.source.stroke_opacity = self._start_stroke_opacity
        self.source.interpolate(self.target, eased)

    def finish(self) -> None:
        self.source.points = self.target.points.copy()
        self.source.subpaths = [s.copy() for s in self.target.subpaths]
        self.source.stroke_color = self.target.stroke_color
        self.source.fill_color = self.target.fill_color
        self.source.stroke_width = self.target.stroke_width
        self.source.fill_opacity = self.target.fill_opacity
        self.source.stroke_opacity = self.target.stroke_opacity


class ShiftAnim:
    """Translate VMobject or VGroup by (dx, dy) over run_time."""

    def __init__(
        self,
        target: Union[VMobject, VGroup],
        dx: float,
        dy: float,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self.target = target
        self.dx = dx
        self.dy = dy
        self.run_time = run_time
        self.rate_func = rate_func
        self._mobs: list[VMobject] = []
        self._snap_points: list[np.ndarray] = []
        self._snap_subpaths: list[list[np.ndarray]] = []

    @property
    def mobjects(self) -> list[VMobject]:
        return self._mobs

    def begin(self) -> None:
        self._mobs = _iter_vmobjects(self.target)
        self._snap_points = [m.points.copy() for m in self._mobs]
        self._snap_subpaths = [[s.copy() for s in m.subpaths] for m in self._mobs]

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        d = np.array([self.dx * eased, self.dy * eased])
        for m, pts, subs in zip(self._mobs, self._snap_points, self._snap_subpaths):
            m.points = pts + d
            m.subpaths = [s + d for s in subs]

    def finish(self) -> None:
        self.interpolate(1.0)


class FadeIn:
    """Fade a VMobject or VGroup from 0 opacity to its current opacity over run_time."""

    def __init__(
        self,
        target: Union[VMobject, VGroup],
        run_time: float = 0.5,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self.target = target
        self.run_time = run_time
        self.rate_func = rate_func
        self._mobs: list[VMobject] = []
        self._target_fill: list[float] = []
        self._target_stroke: list[float] = []

    @property
    def mobjects(self) -> list[VMobject]:
        return self._mobs

    def begin(self) -> None:
        self._mobs = _iter_vmobjects(self.target)
        self._target_fill = [m.fill_opacity for m in self._mobs]
        self._target_stroke = [m.stroke_opacity for m in self._mobs]
        for m in self._mobs:
            m.fill_opacity = 0.0
            m.stroke_opacity = 0.0

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        for m, fo, so in zip(self._mobs, self._target_fill, self._target_stroke):
            m.fill_opacity = eased * fo
            m.stroke_opacity = eased * so

    def finish(self) -> None:
        for m, fo, so in zip(self._mobs, self._target_fill, self._target_stroke):
            m.fill_opacity = fo
            m.stroke_opacity = so


class Write:
    """Stroke-by-stroke reveal across a VGroup's submobjects.

    Staggers a FadeIn across submobjects with `lag_ratio` controlling overlap:
    - 0.0 → all submobjects fade in simultaneously (same as FadeIn).
    - 1.0 → each submobject finishes before the next begins.

    Single VMobject → equivalent to FadeIn.
    """

    def __init__(
        self,
        target: Union[VMobject, VGroup],
        run_time: float = 1.5,
        lag_ratio: float = 0.4,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self.target = target
        self.run_time = run_time
        self.lag_ratio = max(0.0, min(1.0, lag_ratio))
        self.rate_func = rate_func
        self._units: list[list[VMobject]] = []
        self._target_fill: list[list[float]] = []
        self._target_stroke: list[list[float]] = []

    @property
    def mobjects(self) -> list[VMobject]:
        return [m for unit in self._units for m in unit]

    def begin(self) -> None:
        self._units = _stagger_units(self.target)
        self._target_fill = [[m.fill_opacity for m in u] for u in self._units]
        self._target_stroke = [[m.stroke_opacity for m in u] for u in self._units]
        for u in self._units:
            for m in u:
                m.fill_opacity = 0.0
                m.stroke_opacity = 0.0

    def interpolate(self, alpha: float) -> None:
        n = len(self._units)
        if n == 0:
            return
        per_duration = 1.0 / (1.0 + (n - 1) * self.lag_ratio)
        for i, (unit, fos, sos) in enumerate(
            zip(self._units, self._target_fill, self._target_stroke)
        ):
            t0 = i * self.lag_ratio * per_duration
            local = 0.0 if per_duration <= 0 else (alpha - t0) / per_duration
            local = max(0.0, min(1.0, local))
            eased = self.rate_func(local)
            for m, fo, so in zip(unit, fos, sos):
                m.fill_opacity = eased * fo
                m.stroke_opacity = eased * so

    def finish(self) -> None:
        for unit, fos, sos in zip(self._units, self._target_fill, self._target_stroke):
            for m, fo, so in zip(unit, fos, sos):
                m.fill_opacity = fo
                m.stroke_opacity = so


class FadeOut:
    """Fade a VMobject or VGroup from current opacity to 0 over run_time."""

    def __init__(
        self,
        target: Union[VMobject, VGroup],
        run_time: float = 0.5,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self.target = target
        self.run_time = run_time
        self.rate_func = rate_func
        self._mobs: list[VMobject] = []
        self._start_fill: list[float] = []
        self._start_stroke: list[float] = []

    @property
    def mobjects(self) -> list[VMobject]:
        return self._mobs

    def begin(self) -> None:
        self._mobs = _iter_vmobjects(self.target)
        self._start_fill = [m.fill_opacity for m in self._mobs]
        self._start_stroke = [m.stroke_opacity for m in self._mobs]

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        for m, fo, so in zip(self._mobs, self._start_fill, self._start_stroke):
            m.fill_opacity = (1.0 - eased) * fo
            m.stroke_opacity = (1.0 - eased) * so

    def finish(self) -> None:
        for m in self._mobs:
            m.fill_opacity = 0.0
            m.stroke_opacity = 0.0
