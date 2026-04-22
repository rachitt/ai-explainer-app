import json
from pathlib import Path

import typer
from pedagogica_schemas.registry import SCHEMA_REGISTRY
from pydantic import ValidationError

from pedagogica_tools._trace import append_event
from pedagogica_tools._view import render_timeline

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
    try:
        typer.echo(render_timeline(job_id), nl=False)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=2) from e


@app.command("chalk-render")
def chalk_render(
    code_path: str = typer.Argument(..., help="Path to the chalk scene .py file."),
    scene_class: str = typer.Argument(..., help="Scene class name inside the file."),
    output: str = typer.Argument(..., help="Output .mp4 path."),
    scene_id: str = typer.Option(..., "--scene-id", help="Scene id for CompileResult."),
    attempt_number: int = typer.Option(1, "--attempt", help="Compile attempt number (1..N)."),
    result_json: str | None = typer.Option(
        None, "--result-json", help="Where to write the CompileResult JSON."
    ),
    cpu_limit: int = typer.Option(300, help="CPU seconds (rlimit)."),
    wall_limit: int = typer.Option(300, help="Wall-clock seconds."),
    memory_limit_mb: int = typer.Option(4096, help="Memory cap in MB (best-effort)."),
    output_size_limit_mb: int = typer.Option(500, help="Max single-file size (RLIMIT_FSIZE)."),
    width: int = typer.Option(1280, help="Frame width in pixels."),
    height: int = typer.Option(720, help="Frame height in pixels."),
    fps: int = typer.Option(30, help="Frames per second."),
    sandbox_profile: str | None = typer.Option(
        None, "--sandbox-profile", help="Override sandbox/chalk.sb path."
    ),
) -> None:
    """Render a chalk scene inside the sandbox-exec profile.

    Exit codes: 0 = render succeeded, 1 = compile failure.
    """
    from pedagogica_tools.chalk_render import RenderOptions, render as chalk_render_fn

    result = chalk_render_fn(
        code_path=code_path,
        scene_class=scene_class,
        output_path=output,
        scene_id=scene_id,
        attempt_number=attempt_number,
        options=RenderOptions(
            cpu_limit=cpu_limit,
            wall_limit=wall_limit,
            memory_limit_mb=memory_limit_mb,
            output_size_limit_mb=output_size_limit_mb,
            width=width,
            height=height,
            fps=fps,
            sandbox_profile=Path(sandbox_profile) if sandbox_profile else None,
        ),
        result_json_path=result_json,
    )
    typer.echo(result.model_dump_json(indent=2))
    if not result.success:
        raise typer.Exit(code=1)


@app.command("elevenlabs-tts")
def elevenlabs_tts(
    text_path: str = typer.Argument(..., help="Plain-text file containing narration."),
    voice_id: str = typer.Argument(..., help="ElevenLabs voice ID."),
    output: str = typer.Argument(..., help="Output .mp3 path."),
    scene_id: str = typer.Option(..., "--scene-id", help="Scene id for AudioClip."),
    result_json: str | None = typer.Option(
        None, "--result-json", help="Where to write AudioClip JSON."
    ),
    model_id: str = typer.Option(
        "eleven_multilingual_v2", "--model-id", help="ElevenLabs model ID."
    ),
    char_quota: int = typer.Option(
        10_000, "--char-quota", help="Max chars before refusing (cost guard)."
    ),
    stability: float = typer.Option(0.5, "--stability"),
    similarity_boost: float = typer.Option(0.75, "--similarity-boost"),
) -> None:
    """Call ElevenLabs Speech-Synthesis-with-Timestamps; save mp3 + AudioClip JSON.

    Exit codes: 0 = ok, 1 = API / IO error, 2 = usage error.
    """
    from pedagogica_tools.elevenlabs_tts import TtsOptions, synthesize

    text = Path(text_path).read_text(encoding="utf-8").strip()
    if not text:
        typer.echo(f"empty text file: {text_path}", err=True)
        raise typer.Exit(code=2)

    try:
        clip = synthesize(
            text=text,
            voice_id=voice_id,
            output_mp3_path=output,
            scene_id=scene_id,
            options=TtsOptions(
                model_id=model_id,
                char_quota=char_quota,
                stability=stability,
                similarity_boost=similarity_boost,
            ),
            result_json_path=result_json,
        )
    except (EnvironmentError, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=2) from e
    except Exception as e:  # noqa: BLE001
        typer.echo(f"TTS failed: {e}", err=True)
        raise typer.Exit(code=1) from e

    typer.echo(clip.model_dump_json(indent=2))


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
    try:
        append_event(job_id, event_json)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=2) from e
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
