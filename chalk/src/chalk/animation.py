"""Animation protocol and Transform implementation."""
from __future__ import annotations

from typing import Callable, Protocol, Sequence
import numpy as np

from chalk.mobject import VMobject
from chalk.rate_funcs import smooth


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
        self._start_stroke_color = self.source.stroke_color
        self._start_fill_color = self.source.fill_color
        self._start_stroke_width = self.source.stroke_width
        self._start_fill_opacity = self.source.fill_opacity
        self._start_stroke_opacity = self.source.stroke_opacity

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        assert self._start_points is not None
        # Restore to start state, then let VMobject.interpolate do the lerp
        self.source.points = self._start_points.copy()
        self.source.stroke_color = self._start_stroke_color
        self.source.fill_color = self._start_fill_color
        self.source.stroke_width = self._start_stroke_width
        self.source.fill_opacity = self._start_fill_opacity
        self.source.stroke_opacity = self._start_stroke_opacity
        self.source.interpolate(self.target, eased)

    def finish(self) -> None:
        self.source.points = self.target.points.copy()
        self.source.stroke_color = self.target.stroke_color
        self.source.fill_color = self.target.fill_color
        self.source.stroke_width = self.target.stroke_width
        self.source.fill_opacity = self.target.fill_opacity
        self.source.stroke_opacity = self.target.stroke_opacity
