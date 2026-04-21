import json
from pathlib import Path

import typer
from pedagogica_schemas.registry import SCHEMA_REGISTRY
from pydantic import ValidationError

app = typer.Typer(
    help="Pedagogica pipeline helpers — validate, render, TTS, mux, trace, view.",
    no_args_is_help=True,
)


@app.command()
def validate(
    schema: str = typer.Argument(
        ...,
        help="Schema name from the registry (see `list-schemas`).",
    ),
    path: str = typer.Argument(..., help="Path to the JSON file to validate."),
) -> None:
    """Validate a JSON file against a Pedagogica schema.

    Exit codes: 0 = ok, 1 = validation failed, 2 = usage/IO error.
    """
    if schema == "--list" or schema == "list":
        for name in sorted(SCHEMA_REGISTRY):
            typer.echo(name)
        raise typer.Exit(code=0)

    if schema not in SCHEMA_REGISTRY:
        known = ", ".join(sorted(SCHEMA_REGISTRY))
        typer.echo(f"unknown schema {schema!r}; known: {known}", err=True)
        raise typer.Exit(code=2)

    p = Path(path)
    if not p.is_file():
        typer.echo(f"not a file: {path}", err=True)
        raise typer.Exit(code=2)

    model_cls = SCHEMA_REGISTRY[schema]
    raw = p.read_text()
    try:
        model_cls.model_validate_json(raw)
    except json.JSONDecodeError as e:
        typer.echo(f"invalid JSON in {path}: {e}", err=True)
        raise typer.Exit(code=1) from e
    except ValidationError as e:
        typer.echo(f"{schema} validation failed for {path}:", err=True)
        typer.echo(e.json(indent=2), err=True)
        raise typer.Exit(code=1) from e

    typer.echo(f"ok: {schema} {path}")


@app.command("list-schemas")
def list_schemas() -> None:
    """List every schema name the validator knows about."""
    for name in sorted(SCHEMA_REGISTRY):
        typer.echo(name)


@app.command()
def view(job_id: str) -> None:
    """Print a job's timeline, costs, and skill versions from trace.jsonl."""
    typer.echo(f"[stub] view {job_id}")
    raise typer.Exit(code=2)


@app.command("manim-render")
def manim_render(code_path: str, scene_class: str, output: str) -> None:
    """Render a Manim scene inside the sandbox-exec profile."""
    typer.echo(f"[stub] manim-render {code_path} {scene_class} -> {output}")
    raise typer.Exit(code=2)


@app.command("elevenlabs-tts")
def elevenlabs_tts(text_path: str, voice_id: str, output: str) -> None:
    """Call ElevenLabs Speech-Synthesis-with-Timestamps; save mp3 + timings."""
    typer.echo(f"[stub] elevenlabs-tts {text_path} voice={voice_id} -> {output}")
    raise typer.Exit(code=2)


@app.command("ffmpeg-mux")
def ffmpeg_mux(job_dir: str) -> None:
    """Concat per-scene renders + audio into final.mp4 with crossfades."""
    typer.echo(f"[stub] ffmpeg-mux {job_dir}")
    raise typer.Exit(code=2)


@app.command("subtitle-gen")
def subtitle_gen(job_dir: str) -> None:
    """Generate VTT and SRT files from per-scene word timings."""
    typer.echo(f"[stub] subtitle-gen {job_dir}")
    raise typer.Exit(code=2)


@app.command("measure-drift")
def measure_drift(scene_dir: str) -> None:
    """Measure observed audio-visual drift against sync.json predictions."""
    typer.echo(f"[stub] measure-drift {scene_dir}")
    raise typer.Exit(code=2)


@app.command()
def trace(job_id: str, event_json: str) -> None:
    """Append a single event line to a job's trace.jsonl."""
    typer.echo(f"[stub] trace {job_id} {event_json}")
    raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
