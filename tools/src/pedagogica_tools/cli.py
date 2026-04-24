import json
from pathlib import Path

import typer
from pedagogica_schemas.intake import IntakeResult
from pedagogica_schemas.registry import SCHEMA_REGISTRY
from pedagogica_schemas.script import Script
from pedagogica_schemas.storyboard import Storyboard
from pedagogica_schemas.validators import (
    validate_hook_question_propagation,
    validate_script,
    validate_storyboard_depth,
)
from pydantic import ValidationError

from pedagogica_tools._trace import append_event
from pedagogica_tools._view import render_timeline

app = typer.Typer(
    help="Pedagogica pipeline helpers — validate, render, TTS, mux, trace, view.",
    no_args_is_help=True,
)


def _load_json_model(
    path: str,
    schema_name: str,
    model_cls: type[Script] | type[Storyboard] | type[IntakeResult],
):
    p = Path(path)
    if not p.is_file():
        typer.echo(f"not a file: {path}", err=True)
        raise typer.Exit(code=2)

    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as e:
        typer.echo(f"failed to read {path}: {e}", err=True)
        raise typer.Exit(code=2) from e

    try:
        registry_model = SCHEMA_REGISTRY.get(schema_name)
        if registry_model is not None:
            return registry_model.model_validate_json(raw)
        return model_cls.model_validate(json.loads(raw))
    except (OSError, json.JSONDecodeError, ValidationError) as e:
        typer.echo(f"{schema_name} load failed for {path}: {e}", err=True)
        raise typer.Exit(code=2) from e


def _format_issue_table(issues: list[object]) -> str:
    lines = ["rule | severity | observed | threshold | message"]
    if not issues:
        lines.append("ok | - | - | - | no issues")
        return "\n".join(lines)

    for issue in issues:
        lines.append(
            f"{issue.rule} | {issue.severity} | {issue.observed} | {issue.threshold} | {issue.message}"
        )
    return "\n".join(lines)


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


@app.command("check-hook-question")
def check_hook_question(
    intake_json: str = typer.Argument(..., help="Path to 01_intake.json."),
    storyboard_json: str = typer.Argument(..., help="Path to 03_storyboard.json."),
) -> None:
    """Check that hook_question is copied and anchored in the storyboard.

    Exit codes: 0 = ok or warnings-only, 1 = error issue present, 2 = usage/IO error.
    """
    intake = _load_json_model(intake_json, "IntakeResult", IntakeResult)
    storyboard = _load_json_model(storyboard_json, "Storyboard", Storyboard)

    report = validate_hook_question_propagation(intake, storyboard)
    typer.echo(f"intake: {report.intake_hook_question}")
    typer.echo(f"storyboard: {report.storyboard_hook_question}")
    if not report.issues:
        typer.echo("ok: hook_question propagated")
        return

    for issue in report.issues:
        typer.echo(f"[{issue.severity}] {issue.rule}: {issue.message}")

    if not report.passed:
        raise typer.Exit(code=1)


@app.command("check-script")
def check_script(
    script_path: str,
    storyboard_path: str,
    strict: bool = typer.Option(False, "--strict", help="Exit 1 if any quota fails"),
) -> None:
    """Validate a script's cadence + word budget against its storyboard beat."""
    script = _load_json_model(script_path, "Script", Script)
    storyboard = _load_json_model(storyboard_path, "Storyboard", Storyboard)

    try:
        report = validate_script(script, storyboard)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=2) from e

    typer.echo(_format_issue_table(report.issues))
    typer.echo(
        f"scene={report.scene_id} passed={report.passed} quotas_met={report.quotas_met}/5"
    )
    if not report.passed or (strict and report.issues):
        raise typer.Exit(code=1)


@app.command("check-storyboard")
def check_storyboard(
    storyboard_path: str,
    strict: bool = typer.Option(False, "--strict"),
) -> None:
    """Validate storyboard depth budget."""
    storyboard = _load_json_model(storyboard_path, "Storyboard", Storyboard)
    report = validate_storyboard_depth(storyboard)

    typer.echo(_format_issue_table(report.issues))
    typer.echo(
        "topic="
        f"{report.topic} passed={report.passed} total_duration_seconds={report.total_duration_seconds} "
        f"lo_count_in_depth={report.lo_count_in_depth}"
    )
    if not report.passed or (strict and report.issues):
        raise typer.Exit(code=1)


@app.command()
def view(job_id: str) -> None:
    """Print a job's timeline, costs, and skill versions from trace.jsonl."""
    try:
        typer.echo(render_timeline(job_id), nl=False)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=2) from e


@app.command("audit-skills")
def audit_skills_cmd(
    skills_root: str = typer.Option(
        "pedagogica/skills",
        "--skills-root",
        help="Root directory containing agents/ and knowledge/ subdirs.",
    ),
    strict_body: bool = typer.Option(
        False,
        "--strict-body",
        help="Promote body-ref warnings to errors (exit 1 if any).",
    ),
) -> None:
    """Audit SKILL frontmatter for drift (name mismatch, dangling requires).

    Exit codes: 0 = clean or warnings-only, 1 = errors or strict-body warnings,
    2 = usage/IO error.
    """
    from pedagogica_tools.audit_skills import audit_skills, format_report

    root = Path(skills_root)
    if not root.is_dir():
        typer.echo(f"not a directory: {skills_root}", err=True)
        raise typer.Exit(code=2)
    if not (root / "agents").is_dir() and not (root / "knowledge").is_dir():
        typer.echo(f"missing agents/ and knowledge/ under: {skills_root}", err=True)
        raise typer.Exit(code=2)

    report = audit_skills(root)
    typer.echo(format_report(report))
    if report.has_errors or (report.has_warnings and strict_body):
        raise typer.Exit(code=1)


def format_audit_summary(
    skill_report,
    artifact_issues: list | None,
    artifact_scanned_count: int | None,
    artifact_skipped_count: int | None,
) -> str:
    from pedagogica_tools.audit_skills import format_report

    lines = ["SKILL audit", format_report(skill_report), "", "artifact audit"]
    if artifact_issues is None:
        lines.append("skipped (no job_dir)")
    else:
        for issue in artifact_issues:
            lines.append(str(issue.path))
            lines.append(f"  [{issue.schema}] {issue.message}")
        lines.append(
            f"{artifact_scanned_count} artifacts scanned, "
            f"{len(artifact_issues)} issues, skipped count={artifact_skipped_count}."
        )

    issue_count = sum(
        1
        for issue in skill_report.issues
        if issue.severity in {"error", "warning"}
    )
    issue_count += len(artifact_issues or [])
    lines.append("")
    if issue_count:
        lines.append(f"overall: {issue_count} issues")
    else:
        lines.append("overall: clean")
    return "\n".join(lines)


@app.command("audit")
def audit_cmd(
    job_dir: str | None = typer.Argument(None, help="Artifact job directory to audit."),
    skills_root: str = typer.Option(
        "pedagogica/skills",
        "--skills-root",
        help="Root directory containing agents/ and knowledge/ subdirs.",
    ),
    strict_body: bool = typer.Option(
        True,
        "--strict-body/--no-strict-body",
        help="Promote body-ref warnings to errors.",
    ),
) -> None:
    """Run the SKILL audit and, optionally, schema-validate job artifacts.

    Exit codes: 0 = clean, 1 = audit issues, 2 = usage/IO error.
    """
    from pedagogica_tools.audit_artifacts import audit_artifacts, count_unknown_artifacts
    from pedagogica_tools.audit_skills import audit_skills

    root = Path(skills_root)
    if not root.is_dir():
        typer.echo(f"not a directory: {skills_root}", err=True)
        raise typer.Exit(code=2)
    if not (root / "agents").is_dir() and not (root / "knowledge").is_dir():
        typer.echo(f"missing agents/ and knowledge/ under: {skills_root}", err=True)
        raise typer.Exit(code=2)

    artifact_issues = None
    artifact_scanned_count = None
    artifact_skipped_count = None
    if job_dir is not None:
        artifact_root = Path(job_dir)
        if not artifact_root.is_dir():
            typer.echo(f"not a directory: {job_dir}", err=True)
            raise typer.Exit(code=2)
        artifact_issues, artifact_scanned_count = audit_artifacts(artifact_root)
        artifact_skipped_count = count_unknown_artifacts(artifact_root)

    skill_report = audit_skills(root)
    typer.echo(
        format_audit_summary(
            skill_report,
            artifact_issues,
            artifact_scanned_count,
            artifact_skipped_count,
        )
    )
    if (
        skill_report.has_errors
        or (strict_body and skill_report.has_warnings)
        or bool(artifact_issues)
    ):
        raise typer.Exit(code=1)


@app.command("list-skills")
def list_skills_cmd(
    skills_root: str = typer.Option(
        "pedagogica/skills",
        "--skills-root",
        help="Root directory containing agents/ and knowledge/ subdirs.",
    ),
    category: str | None = typer.Option(
        None,
        "--category",
        help="Filter by category: 'agents' or 'knowledge'.",
    ),
) -> None:
    """Print the SKILL roster as a table. Exit codes: 0 = ok, 2 = usage/IO error."""
    from pedagogica_tools.audit_skills import format_roster, iter_skill_files, parse_skill

    root = Path(skills_root)
    if not root.is_dir():
        typer.echo(f"not a directory: {skills_root}", err=True)
        raise typer.Exit(code=2)

    if category is not None and category not in {"agents", "knowledge"}:
        typer.echo("invalid category: expected 'agents' or 'knowledge'", err=True)
        raise typer.Exit(code=2)

    skills = []
    for path in iter_skill_files(root):
        skill, issues = parse_skill(path)
        if issues:
            for issue in issues:
                typer.echo(f"{issue.skill_path}: {issue.message}", err=True)
            raise typer.Exit(code=2)
        if skill is not None:
            skills.append(skill)

    if category is not None:
        skills = [skill for skill in skills if skill.category == category]

    typer.echo(format_roster(skills))


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
    target_duration_seconds: float | None = typer.Option(
        None,
        "--target-duration-seconds",
        help="Scene target duration in seconds for post-render quality gates.",
    ),
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
            target_duration_seconds=target_duration_seconds,
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
    speed: float = typer.Option(
        0.75,
        "--speed",
        help=(
            "Speech rate multiplier (0.7-1.2). "
            "Default 0.75 is the calm explainer pace; 0.9 or 1.0 for faster delivery."
        ),
    ),
    pronounce: bool = typer.Option(
        True,
        "--pronounce/--no-pronounce",
        help=(
            "Apply default pronunciation-hint dict before calling ElevenLabs "
            "(default on). Pass --no-pronounce for old behaviour."
        ),
    ),
) -> None:
    """Call ElevenLabs Speech-Synthesis-with-Timestamps; save mp3 + AudioClip JSON.

    Exit codes: 0 = ok, 1 = API / IO error, 2 = usage error.
    """
    from pedagogica_tools.elevenlabs_tts import TtsOptions, synthesize
    from pedagogica_tools.tts_preproc import apply_rules

    path = Path(text_path)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        typer.echo(f"empty text file: {text_path}", err=True)
        raise typer.Exit(code=2)

    if pronounce:
        try:
            rewritten, fired_rules = apply_rules(text)
        except ValueError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=2) from e

        original_word_count = len(text.split())
        rewritten_word_count = len(rewritten.split())
        if rewritten_word_count != original_word_count:
            alignment_breakers = []
            for rule in fired_rules:
                probe, _ = apply_rules(text, [rule])
                if len(probe.split()) != original_word_count:
                    alignment_breakers.append(rule)
            broken_rules = alignment_breakers or fired_rules
            fired = ", ".join(
                f"{rule.pattern} -> {rule.replacement} ({rule.reason})"
                for rule in broken_rules
            )
            typer.echo(
                "pronunciation preprocessing changed word count "
                f"from {original_word_count} to {rewritten_word_count}; "
                f"rules that broke alignment: {fired or 'none'}",
                err=True,
            )
            raise typer.Exit(code=2)

        rewritten_path = path.with_name(f"{path.name}.rewritten.txt")
        rewritten_path.write_text(rewritten, encoding="utf-8")
        if fired_rules:
            fired = ", ".join(
                f"{rule.pattern} -> {rule.replacement} ({rule.reason})"
                for rule in fired_rules
            )
        else:
            fired = "none"
        typer.echo(f"pronunciation rules fired: {fired}", err=True)
        text = rewritten

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
                speed=speed,
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
    no_final: bool = typer.Option(False, "--no-final", help="Skip job-level captions.vtt/captions.srt."),
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


@app.command("check-duration")
def check_duration(
    job_dir: str = typer.Argument(..., help="Artifact job directory."),
    threshold: float = typer.Option(
        0.15, help="Drift fraction beyond which a scene is flagged (default 0.15 = 15%)."
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help=(
            "Exit 1 if any scene is over threshold or has a broken render "
            "(default: warn-only exit 0)."
        ),
    ),
) -> None:
    """Report per-scene |video_duration - target_duration| drift from latest CompileResult.

    Exit codes: 0 = ok, 1 = over threshold or broken render under --strict, 2 = usage/IO error.
    """
    from pedagogica_tools.check_duration import check_job_duration, format_report

    job_path = Path(job_dir)
    if not job_path.is_dir():
        typer.echo(f"not a directory: {job_dir}", err=True)
        raise typer.Exit(code=2)

    scenes_dir = job_path / "scenes"
    if not scenes_dir.is_dir():
        typer.echo(f"no scenes/ in {job_dir}", err=True)
        raise typer.Exit(code=2)

    report = check_job_duration(job_path, threshold=threshold)
    typer.echo(format_report(report))
    if strict and (report.any_over_threshold or report.any_broken_render):
        raise typer.Exit(code=1)


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
