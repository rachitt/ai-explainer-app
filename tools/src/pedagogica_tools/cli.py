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
def ffmpeg_mux(
    job_dir: str = typer.Argument(..., help="Artifact job directory to mux."),
    crossfade_seconds: float = typer.Option(0.0, "--crossfade-seconds"),
    output: str = typer.Option("final.mp4", "--output", help="Final output filename."),
    force: bool = typer.Option(False, "--force", help="Rebuild even when outputs are fresh."),
    scenes_only: bool = typer.Option(
        False, "--scenes-only", help="Only build per-scene synced.mp4."
    ),
    concat_only: bool = typer.Option(
        False, "--concat-only", help="Only concat existing synced.mp4."
    ),
) -> None:
    """Concat per-scene renders + audio into final.mp4 with crossfades."""
    if scenes_only and concat_only:
        typer.echo("--scenes-only and --concat-only are mutually exclusive", err=True)
        raise typer.Exit(code=2)

    from pedagogica_tools.ffmpeg_mux import MuxOptions, mux

    try:
        result = mux(
            job_dir,
            MuxOptions(
                crossfade_seconds=crossfade_seconds,
                output_name=output,
                force=force,
                scenes_only=scenes_only,
                concat_only=concat_only,
            ),
        )
    except NotImplementedError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=2) from e

    if result.ok:
        summary = "ok"
        if result.output_path:
            summary += f": {result.output_path}"
        if result.duration_seconds is not None:
            summary += f" ({result.duration_seconds:.3f}s)"
        typer.echo(summary)
        raise typer.Exit(code=0)

    typer.echo(f"fail: {result.error}", err=True)
    if result.error and (
        result.error == "ffmpeg not found on PATH" or result.error.startswith("ffmpeg failed")
    ):
        raise typer.Exit(code=1)
    raise typer.Exit(code=2)


@app.command("subtitle-gen")
def subtitle_gen(
    job_dir: str = typer.Argument(..., help="Artifact job directory to subtitle."),
    max_chars_per_line: int = typer.Option(42, "--max-chars-per-line"),
    max_lines: int = typer.Option(2, "--max-lines"),
    min_cue_seconds: float = typer.Option(1.0, "--min-cue-seconds"),
    max_cue_seconds: float = typer.Option(6.0, "--max-cue-seconds"),
    force: bool = typer.Option(False, "--force", help="Rebuild even when outputs are fresh."),
    no_final: bool = typer.Option(False, "--no-final", help="Skip job-level final.vtt/final.srt."),
) -> None:
    """Generate VTT and SRT files from per-scene word timings."""
    from pedagogica_tools.subtitle_gen import SubtitleOptions, generate

    result = generate(
        job_dir,
        SubtitleOptions(
            max_chars_per_line=max_chars_per_line,
            max_lines_per_cue=max_lines,
            min_cue_seconds=min_cue_seconds,
            max_cue_seconds=max_cue_seconds,
            force=force,
            emit_job_final=not no_final,
        ),
    )

    if result.ok:
        typer.echo(
            f"ok: {len(result.scene_vtt_paths)} scene VTT, "
            f"{len(result.scene_srt_paths)} scene SRT"
        )
        if result.final_vtt_path:
            typer.echo(f"final vtt: {result.final_vtt_path}")
        if result.final_srt_path:
            typer.echo(f"final srt: {result.final_srt_path}")
        raise typer.Exit(code=0)

    typer.echo(f"fail: {result.error}", err=True)
    if result.error and (
        result.error.startswith("missing")
        or result.error.startswith("invalid clip.json")
        or result.error.startswith("job dir does not exist")
        or result.error.startswith("scenes dir does not exist")
        or result.error.startswith("no scene dirs found")
    ):
        raise typer.Exit(code=2)
    raise typer.Exit(code=1)


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
