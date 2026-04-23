"""chalk CLI: render a Scene subclass to MP4 and/or live preview."""
from __future__ import annotations

import importlib.util
import inspect
import json
import sys
import warnings
from pathlib import Path
from typing import Optional

import typer

from chalk.axes import Axes
from chalk.camera import Camera2D
from chalk.layout import _bbox, check_bbox_overlap
from chalk.output import FFmpegSink, PreviewSink, TeeSink
from chalk.scene import Scene
from chalk.shapes import Dot, Line
from chalk.vgroup import VGroup

# Markers (dots, ticks, small annotations) land semantically on top of other
# objects by design. Overlaps where one partner's bbox area falls under this
# threshold are treated as intentional and skipped by the preflight gate.
_MARKER_AREA_THRESHOLD = 0.08  # ~0.28 × 0.28 world units

app = typer.Typer(help="chalk — educational animation renderer")


def _load_scene(file_path: Path, scene_name: str) -> type[Scene]:
    spec = importlib.util.spec_from_file_location("_chalk_user_scene", file_path)
    if spec is None or spec.loader is None:
        raise typer.BadParameter(f"cannot load {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_chalk_user_scene"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    cls = getattr(mod, scene_name, None)
    if cls is None:
        raise typer.BadParameter(f"no class '{scene_name}' in {file_path}")
    if not (inspect.isclass(cls) and issubclass(cls, Scene)):
        raise typer.BadParameter(f"'{scene_name}' is not a Scene subclass")
    return cls  # type: ignore[return-value]


def _snapshot(scene: Scene, name: str) -> dict:
    return {"name": name, "mobjects": list(scene._mobjects)}


def _mob_label(mob: object, idx: int) -> str:
    return f"{idx}:{repr(mob)}"


def _bbox_area(mob: object) -> float:
    xmin, ymin, xmax, ymax = _bbox(mob)
    return max(0.0, xmax - xmin) * max(0.0, ymax - ymin)


def _pair_ignored(
    a: object,
    b: object,
    *,
    plot_curve_ids: set[int],
    table_child_sets: list[set[int]],
) -> bool:
    if isinstance(a, Line) and isinstance(b, Line):
        return True
    if (isinstance(a, Line) and id(b) in plot_curve_ids) or (
        isinstance(b, Line) and id(a) in plot_curve_ids
    ):
        return True
    # Multiple plot curves frequently overlap on purpose (e.g. three
    # trajectories on the same axes, a function vs its approximation).
    if id(a) in plot_curve_ids and id(b) in plot_curve_ids:
        return True
    if isinstance(a, Dot) or isinstance(b, Dot):
        return True
    if min(_bbox_area(a), _bbox_area(b)) < _MARKER_AREA_THRESHOLD:
        return True
    aid = id(a)
    bid = id(b)
    return any(aid in child_set and bid in child_set for child_set in table_child_sets)


def _run_preflight(
    scene_cls: type[Scene],
    *,
    scene_module: object | None,
    preflight_json: Path | None,
) -> tuple[bool, int, int]:
    snapshots: list[dict] = []
    plot_curve_ids: set[int] = set()
    table_child_sets: list[set[int]] = []

    import chalk.axes as axes_mod

    original_plot_function = axes_mod.plot_function

    def plot_function_wrapper(*args, **kwargs):
        curve = original_plot_function(*args, **kwargs)
        if args and isinstance(args[0], Axes):
            plot_curve_ids.add(id(curve))
        return curve

    axes_mod.plot_function = plot_function_wrapper
    had_module_plot = scene_module is not None and hasattr(scene_module, "plot_function")
    module_plot = getattr(scene_module, "plot_function", None) if had_module_plot else None
    if had_module_plot:
        setattr(scene_module, "plot_function", plot_function_wrapper)

    instance: Scene = scene_cls()

    original_add = instance.add

    def add_with_table_tracking(*mobjects):
        for mob in mobjects:
            if isinstance(mob, VGroup):
                child_ids = {id(leaf) for leaf in instance._flatten(mob)}
                if len(child_ids) > 1:
                    table_child_sets.append(child_ids)
        original_add(*mobjects)

    def play_noop(*animations, run_time=None):
        return None

    def wait_noop(duration: float = 1.0, **kwargs):
        return None

    def clear_preflight(run_time: float = 0.5, keep: list | None = None):
        snapshots.append(_snapshot(instance, "clear"))
        keep_ids: set[int] = set()
        for k in (keep or []):
            for leaf in instance._flatten(k):
                keep_ids.add(id(leaf))
        keep_rd_ids = {id(k) for k in (keep or [])}
        instance._mobjects = [m for m in instance._mobjects if id(m) in keep_ids]
        instance._redrawables = [
            rd for rd in instance._redrawables if id(rd) in keep_rd_ids
        ]

    def section_preflight(name: str):
        snapshots.append(_snapshot(instance, name))
        instance._sections.append((name, instance._frame_index))

    instance.add = add_with_table_tracking  # type: ignore[method-assign]
    instance.play = play_noop  # type: ignore[method-assign]
    instance.wait = wait_noop  # type: ignore[method-assign]
    instance.clear = clear_preflight  # type: ignore[method-assign]
    instance.section = section_preflight  # type: ignore[method-assign]

    try:
        instance.construct()
    finally:
        axes_mod.plot_function = original_plot_function
        if had_module_plot:
            setattr(scene_module, "plot_function", module_plot)

    snapshots.append(_snapshot(instance, "final"))

    sections_report = []
    any_failure = False
    peak = 0
    for snap in snapshots:
        name = snap["name"]
        mobs = list(snap["mobjects"])
        peak = max(peak, len(mobs))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            raw_overlaps = check_bbox_overlap(mobs, padding=0.05)
        overlaps = []
        for i, j, rect in raw_overlaps:
            if _pair_ignored(
                mobs[i],
                mobs[j],
                plot_curve_ids=plot_curve_ids,
                table_child_sets=table_child_sets,
            ):
                continue
            overlaps.append(
                {
                    "pair": [_mob_label(mobs[i], i), _mob_label(mobs[j], j)],
                    "rect": rect,
                }
            )
            typer.echo(
                "preflight overlap: "
                f"section={name} pair={_mob_label(mobs[i], i)}-"
                f"{_mob_label(mobs[j], j)} rect={rect}",
                err=True,
            )

        off_frame = []
        for i, mob in enumerate(mobs):
            if isinstance(mob, Line):
                continue
            bbox = _bbox(mob)
            if bbox == (0.0, 0.0, 0.0, 0.0):
                continue
            xmin, ymin, xmax, ymax = bbox
            if xmin < -7.1 or xmax > 7.1 or ymin < -4.0 or ymax > 4.0:
                off_frame.append({"mob": _mob_label(mob, i), "bbox": bbox})
                typer.echo(
                    "preflight offframe: "
                    f"section={name} mob={_mob_label(mob, i)} bbox={bbox}",
                    err=True,
                )

        if overlaps or off_frame:
            any_failure = True
        sections_report.append(
            {"name": name, "overlaps": overlaps, "offframe": off_frame}
        )

    if preflight_json is not None:
        preflight_json.parent.mkdir(parents=True, exist_ok=True)
        preflight_json.write_text(
            json.dumps({"sections": sections_report}, indent=2),
            encoding="utf-8",
        )

    return (not any_failure, len(snapshots), peak)


@app.command()
def render(
    file: Path = typer.Argument(..., help="Python file containing the Scene subclass"),
    scene: str = typer.Option("Scene", "--scene", "-s", help="Scene class name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output MP4 path"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Show live preview window"),
    fps: int = typer.Option(30, "--fps", help="Frames per second"),
    width: int = typer.Option(1920, "--width", help="Frame width in pixels"),
    height: int = typer.Option(1080, "--height", help="Frame height in pixels"),
    preflight: bool = typer.Option(
        False,
        "--preflight",
        help="Run layout preflight only: no render, play/wait stubbed.",
    ),
    preflight_json: Optional[Path] = typer.Option(
        None,
        "--preflight-json",
        help="Write preflight section report JSON to this path.",
    ),
) -> None:
    """Render a chalk Scene to MP4 and/or live preview window."""
    if not preflight and not preview and output is None:
        typer.echo("Error: specify --preview and/or -o <output.mp4>", err=True)
        raise typer.Exit(1)

    scene_cls = _load_scene(file, scene)
    if preflight:
        scene_module = sys.modules.get("_chalk_user_scene")
        ok, n_sections, peak = _run_preflight(
            scene_cls,
            scene_module=scene_module,
            preflight_json=preflight_json,
        )
        if ok:
            typer.echo(f"preflight ok: {n_sections} sections, {peak} mobjects peak")
            raise typer.Exit(0)
        raise typer.Exit(1)

    camera = Camera2D(pixel_width=width, pixel_height=height)

    sinks: list = []
    if output is not None:
        sinks.append(FFmpegSink(str(output), fps=fps, width=width, height=height))
    if preview:
        sinks.append(PreviewSink(width=width, height=height))

    sink = sinks[0] if len(sinks) == 1 else TeeSink(sinks)

    instance: Scene = scene_cls()
    instance._attach(sink, camera=camera, fps=fps)
    instance.construct()

    sink.close()

    if output is not None:
        typer.echo(f"Wrote {output}")
