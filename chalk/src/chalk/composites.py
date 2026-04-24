"""Composite animation primitives built from Chalk's base animations."""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np

from chalk.animation import (
    Animation,
    AnimationGroup,
    FadeIn,
    Indicate,
    LaggedStart,
    Succession,
    Write,
    _iter_vmobjects,
)
from chalk.axes import plot_function
from chalk.mobject import VMobject
from chalk.rate_funcs import there_and_back
from chalk.vgroup import VGroup


Target = VMobject | VGroup


def _auto_group_run_time(animations: Sequence[Animation], lag_ratio: float) -> float:
    delay = 0.0
    end = 0.0
    for anim in animations:
        end = max(end, delay + anim.run_time)
        delay += lag_ratio * anim.run_time
    return end


def _rescale_run_times(animations: Sequence[Animation], total_run_time: float, lag_ratio: float) -> None:
    auto_total = _auto_group_run_time(animations, lag_ratio)
    if auto_total <= 1e-9:
        return
    scale = total_run_time / auto_total
    for anim in animations:
        anim.run_time *= scale


def _target_center(target: Target) -> np.ndarray:
    leaves = _iter_vmobjects(target)
    all_pts = [mob.points for mob in leaves if len(mob.points) > 0]
    if not all_pts:
        return np.zeros(2)
    return np.mean(np.concatenate(all_pts, axis=0), axis=0)


def _move_target_to(target: Target, x: float, y: float) -> None:
    if hasattr(target, "move_to"):
        target.move_to(x, y)  # type: ignore[call-arg]
        return
    leaves = _iter_vmobjects(target)
    all_pts = [mob.points for mob in leaves if len(mob.points) > 0]
    if not all_pts:
        return
    pts = np.concatenate(all_pts, axis=0)
    cx = float((pts[:, 0].min() + pts[:, 0].max()) / 2)
    cy = float((pts[:, 1].min() + pts[:, 1].max()) / 2)
    target.shift(x - cx, y - cy)


class _Hold:
    """Time-only animation that leaves the target untouched."""

    def __init__(self, target: Target, run_time: float) -> None:
        self.target = target
        self.run_time = run_time

    @property
    def mobjects(self) -> Sequence[VMobject]:
        return _iter_vmobjects(self.target)

    def begin(self) -> None:
        return None

    def interpolate(self, alpha: float) -> None:
        return None

    def finish(self) -> None:
        return None


class _Scale:
    """Pulse a target's geometry around its center, then restore it."""

    def __init__(self, target: Target, scale_factor: float, run_time: float) -> None:
        self.target = target
        self.scale_factor = scale_factor
        self.run_time = run_time
        self._mobs: list[VMobject] = []
        self._snap_points: list[np.ndarray] = []
        self._snap_subpaths: list[list[np.ndarray]] = []
        self._center = np.zeros(2)

    @property
    def mobjects(self) -> Sequence[VMobject]:
        return self._mobs

    def begin(self) -> None:
        self._mobs = _iter_vmobjects(self.target)
        self._snap_points = [mob.points.copy() for mob in self._mobs]
        self._snap_subpaths = [[sub.copy() for sub in mob.subpaths] for mob in self._mobs]
        self._center = _target_center(self.target)

    def interpolate(self, alpha: float) -> None:
        eased = there_and_back(alpha)
        factor = 1.0 + (self.scale_factor - 1.0) * eased
        for mob, pts, subs in zip(self._mobs, self._snap_points, self._snap_subpaths):
            mob.points = (pts - self._center) * factor + self._center
            mob.subpaths = [(sub - self._center) * factor + self._center for sub in subs]

    def finish(self) -> None:
        for mob, pts, subs in zip(self._mobs, self._snap_points, self._snap_subpaths):
            mob.points = pts.copy()
            mob.subpaths = [sub.copy() for sub in subs]


def reveal_then_explain(
    target: Target,
    label: Target,
    *,
    explain_text: Target | None = None,
    run_time: float = 2.0,
) -> LaggedStart:
    animations: list[Animation] = [Write(target), Write(label)]
    if explain_text is not None:
        animations.append(FadeIn(explain_text))
    _rescale_run_times(animations, run_time, lag_ratio=0.35)
    return LaggedStart(*animations, lag_ratio=0.35)


def highlight_and_hold(
    target: Target,
    *,
    color: str | None = None,
    hold_seconds: float = 1.5,
    indicate_run_time: float = 0.8,
) -> Succession:
    if color is None:
        indicate = Indicate(target, run_time=indicate_run_time)
    else:
        indicate = Indicate(target, run_time=indicate_run_time, color=color)
    return Succession(indicate, _Hold(target, run_time=hold_seconds))


def annotated_trace(
    axes,
    fn: Callable[[float], float],
    *,
    x_start: float,
    x_end: float,
    samples: int = 60,
    annotations: list[tuple[float, Target]] | None = None,
    run_time: float = 3.0,
) -> tuple[Animation, VMobject]:
    if hasattr(axes, "plot_function"):
        curve = axes.plot_function(  # type: ignore[attr-defined]
            fn,
            x_range=[x_start, x_end],
            num_sample_points=samples,
        )
    else:
        curve = plot_function(
            axes,
            fn,
            x_start=x_start,
            x_end=x_end,
            resolution=samples,
        )

    if not annotations:
        return Write(curve, run_time=run_time), curve

    for x_val, label in annotations:
        if hasattr(axes, "coords_to_point"):
            point = axes.coords_to_point(x_val, fn(x_val))  # type: ignore[attr-defined]
        else:
            point = axes.to_point(x_val, fn(x_val))
        _move_target_to(label, float(point[0]), float(point[1]))

    lag_ratio = max(0.1, min(0.4, 1.0 / (len(annotations) + 1)))
    animations: list[Animation] = [Write(curve)]
    animations.extend(FadeIn(label) for _, label in annotations)
    _rescale_run_times(animations, run_time, lag_ratio=lag_ratio)
    return LaggedStart(*animations, lag_ratio=lag_ratio), curve


def animated_wait_with_pulse(
    targets: Target | list[Target],
    *,
    pad_seconds: float,
    pulse_every: float = 0.8,
    pulse_scale: float = 1.08,
) -> Succession:
    normalized = targets if isinstance(targets, list) else [targets]
    n_pulses = max(1, int(pad_seconds / pulse_every))
    pulse_run_time = pad_seconds / n_pulses

    pulses: list[Animation] = []
    for _ in range(n_pulses):
        if len(normalized) == 1:
            pulses.append(_Scale(normalized[0], pulse_scale, pulse_run_time))
        else:
            pulses.append(
                AnimationGroup(
                    *[_Scale(target, pulse_scale, pulse_run_time) for target in normalized],
                    lag_ratio=0.0,
                )
            )
    return Succession(*pulses)


def build_up_sequence(
    steps: list[tuple[Target] | tuple[Target, type]],
    *,
    step_run_time: float = 1.0,
    inter_step_pause: float = 0.3,
) -> Succession:
    animations: list[Animation] = []
    for index, step in enumerate(steps):
        mob = step[0]
        animation_cls = step[1] if len(step) > 1 else Write
        animations.append(animation_cls(mob, run_time=step_run_time))
        if index < len(steps) - 1:
            animations.append(_Hold(mob, run_time=inter_step_pause))
    return Succession(*animations)
