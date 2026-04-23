"""Animation protocol and Transform implementation."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Protocol, Sequence, Union
import math
import numpy as np

from chalk.mobject import VMobject
from chalk.rate_funcs import smooth, there_and_back
from chalk.vgroup import VGroup

if TYPE_CHECKING:
    from chalk.value_tracker import ValueTracker
    from chalk.scene import Scene


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

    Internally delegates to LaggedStart(FadeIn(unit) for unit in units).
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
        self._delegate: "LaggedStart | None" = None

    def _build_delegate(self) -> "LaggedStart":
        units = _stagger_units(self.target)
        n = len(units)
        if n == 0:
            return LaggedStart(
                FadeIn(self.target, run_time=self.run_time, rate_func=self.rate_func),
                lag_ratio=self.lag_ratio,
            )
        # Compute per-unit duration so total fits exactly in self.run_time:
        # run_time = per_duration * (1 + (n-1) * lag_ratio)
        per_duration = self.run_time / max(1.0 + (n - 1) * self.lag_ratio, 1e-9)
        sub_anims = [
            FadeIn(VGroup(*unit_mobs), run_time=per_duration, rate_func=self.rate_func)
            for unit_mobs in units
        ]
        return LaggedStart(*sub_anims, lag_ratio=self.lag_ratio)

    @property
    def mobjects(self) -> list[VMobject]:
        if self._delegate is not None:
            return self._delegate.mobjects
        return _iter_vmobjects(self.target)

    def begin(self) -> None:
        self._delegate = self._build_delegate()
        self._delegate.begin()

    def interpolate(self, alpha: float) -> None:
        if self._delegate is not None:
            self._delegate.interpolate(alpha)

    def finish(self) -> None:
        if self._delegate is not None:
            self._delegate.finish()


def _centroid(mob: Union[VMobject, VGroup]) -> np.ndarray:
    """Return the centroid (mean of all leaf points) of a mob or VGroup."""
    leaves = _iter_vmobjects(mob)
    all_pts = [m.points for m in leaves if len(m.points) > 0]
    if not all_pts:
        return np.zeros(2)
    return np.mean(np.concatenate(all_pts, axis=0), axis=0)


class MoveAlongPath:
    """Translate mob so its centroid follows the arc-length parameterization of path."""

    def __init__(
        self,
        mob: Union[VMobject, VGroup],
        path: VMobject,
        run_time: float = 2.0,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self.mob = mob
        self.path = path
        self.run_time = run_time
        self.rate_func = rate_func
        self._mobs: list[VMobject] = []
        self._snap_points: list[np.ndarray] = []
        self._snap_subpaths: list[list[np.ndarray]] = []
        self._path_start: np.ndarray = np.zeros(2)

    @property
    def mobjects(self) -> list[VMobject]:
        return self._mobs

    def begin(self) -> None:
        from chalk.path_utils import arclength_point
        self._mobs = _iter_vmobjects(self.mob)
        self._snap_points = [m.points.copy() for m in self._mobs]
        self._snap_subpaths = [[s.copy() for s in m.subpaths] for m in self._mobs]
        self._path_start = arclength_point(self.path, 0.0).copy()

    def interpolate(self, alpha: float) -> None:
        from chalk.path_utils import arclength_point
        eased = self.rate_func(alpha)
        target = arclength_point(self.path, eased)
        delta = target - self._path_start
        for m, pts, subs in zip(self._mobs, self._snap_points, self._snap_subpaths):
            m.points = pts + delta
            m.subpaths = [s + delta for s in subs]

    def finish(self) -> None:
        self.interpolate(1.0)


class Rotate:
    """Rotate mob by `angle` radians around `about_point` over run_time."""

    def __init__(
        self,
        mob: Union[VMobject, VGroup],
        angle: float,
        about_point: "tuple[float, float] | None" = None,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self.mob = mob
        self.angle = angle
        self.about_point = about_point
        self.run_time = run_time
        self.rate_func = rate_func
        self._mobs: list[VMobject] = []
        self._snap_points: list[np.ndarray] = []
        self._snap_subpaths: list[list[np.ndarray]] = []
        self._center: np.ndarray = np.zeros(2)

    @property
    def mobjects(self) -> list[VMobject]:
        return self._mobs

    def begin(self) -> None:
        self._mobs = _iter_vmobjects(self.mob)
        self._snap_points = [m.points.copy() for m in self._mobs]
        self._snap_subpaths = [[s.copy() for s in m.subpaths] for m in self._mobs]
        if self.about_point is not None:
            self._center = np.array(self.about_point, dtype=float)
        else:
            self._center = _centroid(self.mob)

    def _rot(self, pts: np.ndarray, theta: float) -> np.ndarray:
        c, s = np.cos(theta), np.sin(theta)
        R = np.array([[c, -s], [s, c]])
        return (pts - self._center) @ R.T + self._center

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        theta = self.angle * eased
        for m, pts, subs in zip(self._mobs, self._snap_points, self._snap_subpaths):
            m.points = self._rot(pts, theta)
            m.subpaths = [self._rot(s, theta) for s in subs]

    def finish(self) -> None:
        self.interpolate(1.0)


class ChangeValue:
    """Animate a ValueTracker from its current value to `target` over run_time."""

    def __init__(
        self,
        tracker: "ValueTracker",
        target: float,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self.tracker = tracker
        self.target = float(target)
        self.run_time = run_time
        self.rate_func = rate_func
        self._start: float = 0.0

    @property
    def mobjects(self) -> list[VMobject]:
        return []

    def begin(self) -> None:
        self._start = self.tracker.get_value()

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        self.tracker.set_value(self._start + eased * (self.target - self._start))

    def finish(self) -> None:
        self.tracker.set_value(self.target)


class AnimationGroup:
    """Composite of multiple animations running with controlled overlap.

    lag_ratio=0.0 → all start together (parallel).
    lag_ratio=1.0 → each starts only after the previous ends (sequential).
    0 < lag_ratio < 1 → staggered overlap.

    run_time defaults to the time when the last animation ends.
    """

    def __init__(
        self,
        *animations: "Animation",
        lag_ratio: float = 0.0,
        run_time: float | None = None,
    ) -> None:
        self._animations = list(animations)
        self.lag_ratio = lag_ratio
        # Compute effective run_time from all animation start/end windows
        if run_time is not None:
            self.run_time = run_time
        elif not animations:
            self.run_time = 0.0
        else:
            self.run_time = self._auto_run_time()

    def _auto_run_time(self) -> float:
        """Total time until the last animation finishes."""
        delay = 0.0
        end = 0.0
        for anim in self._animations:
            end = max(end, delay + anim.run_time)
            delay += self.lag_ratio * anim.run_time
        return max(end, 1e-9)

    def _window(self, i: int, total: float) -> tuple[float, float]:
        """Return (t_start, t_end) in [0, total] for animation i."""
        delay = 0.0
        for j, anim in enumerate(self._animations):
            if j == i:
                return (delay, delay + anim.run_time)
            delay += self.lag_ratio * anim.run_time
        return (0.0, total)

    @property
    def mobjects(self) -> list[VMobject]:
        out: list[VMobject] = []
        for anim in self._animations:
            out.extend(anim.mobjects)
        return out

    def begin(self) -> None:
        for anim in self._animations:
            anim.begin()

    def interpolate(self, global_alpha: float) -> None:
        t = global_alpha * self.run_time
        for i, anim in enumerate(self._animations):
            t_start, t_end = self._window(i, self.run_time)
            span = t_end - t_start
            if span < 1e-9:
                local = 1.0
            else:
                local = max(0.0, min(1.0, (t - t_start) / span))
            anim.interpolate(local)

    def finish(self) -> None:
        for anim in self._animations:
            anim.finish()


class Succession(AnimationGroup):
    """Animations run fully sequentially (lag_ratio=1.0)."""

    def __init__(self, *animations: "Animation") -> None:
        super().__init__(*animations, lag_ratio=1.0)


class LaggedStart(AnimationGroup):
    """Animations start in sequence with a fixed lag_ratio overlap."""

    def __init__(self, *animations: "Animation", lag_ratio: float = 0.3) -> None:
        super().__init__(*animations, lag_ratio=lag_ratio)


class Indicate:
    """Temporarily scale up and recolor a mob, then return to original state.

    Uses there_and_back rate func by default: grows at midpoint, returns by end.
    """

    def __init__(
        self,
        mob: Union[VMobject, VGroup],
        scale_factor: float = 1.2,
        color: str = "#FFD54F",
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = there_and_back,
    ) -> None:
        self.mob = mob
        self.scale_factor = scale_factor
        self.color = color
        self.run_time = run_time
        self.rate_func = rate_func
        self._mobs: list[VMobject] = []
        self._snap_points: list[np.ndarray] = []
        self._snap_subpaths: list[list[np.ndarray]] = []
        self._orig_fill: list[str] = []
        self._orig_stroke: list[str] = []
        self._centers: list[np.ndarray] = []

    @property
    def mobjects(self) -> list[VMobject]:
        return self._mobs

    def begin(self) -> None:
        self._mobs = _iter_vmobjects(self.mob)
        self._snap_points = [m.points.copy() for m in self._mobs]
        self._snap_subpaths = [[s.copy() for s in m.subpaths] for m in self._mobs]
        self._orig_fill = [m.fill_color for m in self._mobs]
        self._orig_stroke = [m.stroke_color for m in self._mobs]
        self._centers = [
            np.mean(pts, axis=0) if len(pts) > 0 else np.zeros(2)
            for pts in self._snap_points
        ]

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        s = 1.0 + (self.scale_factor - 1.0) * eased
        for m, pts, subs, orig_fill, orig_stroke, center in zip(
            self._mobs, self._snap_points, self._snap_subpaths,
            self._orig_fill, self._orig_stroke, self._centers
        ):
            m.points = (pts - center) * s + center
            m.subpaths = [(sp - center) * s + center for sp in subs]
            if eased > 0.01:
                m.fill_color = self.color
                m.stroke_color = self.color
            else:
                m.fill_color = orig_fill
                m.stroke_color = orig_stroke

    def finish(self) -> None:
        for m, pts, subs, orig_fill, orig_stroke in zip(
            self._mobs, self._snap_points, self._snap_subpaths,
            self._orig_fill, self._orig_stroke
        ):
            m.points = pts.copy()
            m.subpaths = [s.copy() for s in subs]
            m.fill_color = orig_fill
            m.stroke_color = orig_stroke


class Flash:
    """Radial burst of short lines emanating from a point."""

    def __init__(
        self,
        point: "tuple[float, float]",
        color: str = "#FFD54F",
        num_lines: int = 12,
        line_length: float = 0.3,
        run_time: float = 0.6,
    ) -> None:
        from chalk.shapes import Line
        self.run_time = run_time
        self.rate_func = smooth
        self._lines: list[VMobject] = []
        self._start_opacities: list[float] = []
        pt = np.array(point, dtype=float)
        for i in range(num_lines):
            angle = 2 * math.pi * i / num_lines
            direction = np.array([math.cos(angle), math.sin(angle)])
            start = pt + 0.05 * direction  # small offset from center
            end = pt + (0.05 + line_length) * direction
            line = Line(
                (float(start[0]), float(start[1])),
                (float(end[0]), float(end[1])),
                color=color, stroke_width=2.0,
            )
            self._lines.append(line)

    @property
    def mobjects(self) -> list[VMobject]:
        return self._lines

    def begin(self) -> None:
        for line in self._lines:
            line.stroke_opacity = 0.0
        self._start_opacities = [0.0] * len(self._lines)

    def interpolate(self, alpha: float) -> None:
        eased = there_and_back(alpha)
        for line in self._lines:
            line.stroke_opacity = eased

    def finish(self) -> None:
        for line in self._lines:
            line.stroke_opacity = 0.0


class Circumscribe:
    """Animated outline (rectangle or circle) drawn around a mob."""

    def __init__(
        self,
        mob: Union[VMobject, VGroup],
        shape: str = "rect",
        color: str = "#FFD54F",
        buff: float = 0.1,
        run_time: float = 1.0,
    ) -> None:
        self.mob = mob
        self.shape = shape
        self.color = color
        self.buff = buff
        self.run_time = run_time
        self.rate_func = smooth
        self._outline: VMobject | None = None

    def _make_outline(self) -> VMobject:
        from chalk.shapes import Rectangle
        from chalk.shapes import Circle as C
        if isinstance(self.mob, VGroup):
            bb = self.mob.bbox()
        else:
            pts = self.mob.points
            bb = (float(pts[:, 0].min()), float(pts[:, 1].min()),
                  float(pts[:, 0].max()), float(pts[:, 1].max()))
        xmin, ymin, xmax, ymax = bb
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2
        if self.shape == "rect":
            w = xmax - xmin + 2 * self.buff
            h = ymax - ymin + 2 * self.buff
            r = Rectangle(width=w, height=h, color=self.color, stroke_width=2.5)
            r.shift(cx, cy)
            return r
        else:  # circle
            radius = max(xmax - xmin, ymax - ymin) / 2 + self.buff
            r = C(radius=radius, color=self.color, stroke_width=2.5)
            r.shift(cx, cy)
            return r

    @property
    def mobjects(self) -> list[VMobject]:
        return [self._outline] if self._outline is not None else []

    def begin(self) -> None:
        self._outline = self._make_outline()
        self._outline.stroke_opacity = 0.0

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        if self._outline is not None:
            # Draw-on effect: appear then hold
            self._outline.stroke_opacity = min(1.0, eased * 2)

    def finish(self) -> None:
        if self._outline is not None:
            self._outline.stroke_opacity = 1.0


class CameraShift:
    """Animate the camera's pan offset by (dx, dy) in world units."""

    def __init__(
        self,
        scene: "Scene",
        dx: float,
        dy: float,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        from chalk.scene import Scene as _Scene  # noqa: F401
        self._camera = scene.camera
        self.dx = dx
        self.dy = dy
        self.run_time = run_time
        self.rate_func = rate_func
        self._start_x: float = 0.0
        self._start_y: float = 0.0

    @property
    def mobjects(self) -> list[VMobject]:
        return []

    def begin(self) -> None:
        self._start_x = self._camera.center_x
        self._start_y = self._camera.center_y

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        self._camera.center_x = self._start_x + self.dx * eased
        self._camera.center_y = self._start_y + self.dy * eased

    def finish(self) -> None:
        self.interpolate(1.0)


class CameraZoom:
    """Animate the camera's zoom level to target_zoom."""

    def __init__(
        self,
        scene: "Scene",
        target_zoom: float,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self._camera = scene.camera
        self.target_zoom = target_zoom
        self.run_time = run_time
        self.rate_func = rate_func
        self._start_zoom: float = 1.0

    @property
    def mobjects(self) -> list[VMobject]:
        return []

    def begin(self) -> None:
        self._start_zoom = self._camera.zoom

    def interpolate(self, alpha: float) -> None:
        eased = self.rate_func(alpha)
        self._camera.zoom = self._start_zoom + (self.target_zoom - self._start_zoom) * eased

    def finish(self) -> None:
        self.interpolate(1.0)


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
