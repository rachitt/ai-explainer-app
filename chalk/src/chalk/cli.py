"""chalk CLI: render a Scene subclass to MP4 and/or live preview."""
from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Optional

import typer

from chalk.camera import Camera2D
from chalk.output import FFmpegSink, PreviewSink, TeeSink
from chalk.scene import Scene

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


@app.command()
def render(
    file: Path = typer.Argument(..., help="Python file containing the Scene subclass"),
    scene: str = typer.Option("Scene", "--scene", "-s", help="Scene class name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output MP4 path"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Show live preview window"),
    fps: int = typer.Option(30, "--fps", help="Frames per second"),
    width: int = typer.Option(1920, "--width", help="Frame width in pixels"),
    height: int = typer.Option(1080, "--height", help="Frame height in pixels"),
) -> None:
    """Render a chalk Scene to MP4 and/or live preview window."""
    if not preview and output is None:
        typer.echo("Error: specify --preview and/or -o <output.mp4>", err=True)
        raise typer.Exit(1)

    scene_cls = _load_scene(file, scene)
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
