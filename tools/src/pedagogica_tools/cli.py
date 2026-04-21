import typer

app = typer.Typer(
    help="Pedagogica pipeline helpers — Manim render, TTS, mux, trace, view.",
    no_args_is_help=True,
)


@app.command()
def validate(schema: str, path: str) -> None:
    """Validate a JSON file against a Pedagogica schema."""
    typer.echo(f"[stub] validate {schema} {path}")
    raise typer.Exit(code=2)


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
