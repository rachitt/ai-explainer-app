"""Generate subtitle sidecars from ElevenLabs word timings."""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from pathlib import Path

from pedagogica_schemas.audio import AudioClip, WordTiming
from pydantic import BaseModel, ValidationError

from pedagogica_tools._trace import append_event


@dataclass
class SubtitleOptions:
    max_chars_per_line: int = 42
    max_lines_per_cue: int = 2
    min_cue_seconds: float = 1.0
    max_cue_seconds: float = 6.0
    force: bool = False
    emit_job_final: bool = True


class SubtitleResult(BaseModel):
    ok: bool
    scene_vtt_paths: list[str] = []
    scene_srt_paths: list[str] = []
    final_vtt_path: str | None = None
    final_srt_path: str | None = None
    error: str | None = None


@dataclass
class SubtitleCue:
    start_seconds: float
    end_seconds: float
    text: str


def format_vtt_time(seconds: float) -> str:
    return _format_time(seconds, separator=".")


def format_srt_time(seconds: float) -> str:
    return _format_time(seconds, separator=",")


def group_word_timings(
    word_timings: list[WordTiming],
    *,
    max_chars_per_line: int,
    max_lines_per_cue: int,
    min_cue_seconds: float,
    max_cue_seconds: float,
) -> list[SubtitleCue]:
    char_budget = max_chars_per_line * max_lines_per_cue
    cues: list[SubtitleCue] = []
    current: list[WordTiming] = []

    for word in word_timings:
        if current and _should_start_new_cue(current, word, char_budget, max_cue_seconds):
            cues.append(_cue_from_words(current, max_chars_per_line, max_lines_per_cue))
            current = []
        current.append(word)

    if current:
        cues.append(_cue_from_words(current, max_chars_per_line, max_lines_per_cue))

    return _coalesce_short_cues(cues, min_cue_seconds, max_chars_per_line, max_lines_per_cue)


def generate(job_dir: str | Path, options: SubtitleOptions) -> SubtitleResult:
    job_path = Path(job_dir).resolve()
    job_id = job_path.name

    if not job_path.is_dir():
        return SubtitleResult(ok=False, error=f"job dir does not exist: {job_path}")

    scenes_root = job_path / "scenes"
    if not scenes_root.is_dir():
        return SubtitleResult(ok=False, error=f"scenes dir does not exist: {scenes_root}")

    scene_dirs = sorted(p for p in scenes_root.iterdir() if p.is_dir())
    if not scene_dirs:
        return SubtitleResult(ok=False, error=f"no scene dirs found: {scenes_root}")

    scene_vtt_paths: list[str] = []
    scene_srt_paths: list[str] = []
    scene_cues: list[tuple[str, AudioClip, list[SubtitleCue]]] = []

    _emit_stage(job_id, "subtitle_gen.scenes", "stage_enter")
    for scene_dir in scene_dirs:
        clip_path = scene_dir / "audio" / "clip.json"
        vtt_path = scene_dir / "subtitles.vtt"
        srt_path = scene_dir / "subtitles.srt"

        if not clip_path.is_file():
            _emit_stage(job_id, "subtitle_gen.scenes", "stage_exit", ok=False)
            return SubtitleResult(ok=False, error=f"missing clip.json: {clip_path}")

        try:
            clip = AudioClip.model_validate_json(clip_path.read_text(encoding="utf-8"))
        except (ValidationError, json.JSONDecodeError) as e:
            _emit_stage(job_id, "subtitle_gen.scenes", "stage_exit", ok=False)
            return SubtitleResult(ok=False, error=f"invalid clip.json {clip_path}: {e}")

        cues = group_word_timings(
            clip.word_timings,
            max_chars_per_line=options.max_chars_per_line,
            max_lines_per_cue=options.max_lines_per_cue,
            min_cue_seconds=options.min_cue_seconds,
            max_cue_seconds=options.max_cue_seconds,
        )
        _extend_last_cue_to_duration(cues, clip.total_duration_seconds)
        scene_cues.append((scene_dir.name, clip, cues))

        if (
            not options.force
            and vtt_path.is_file()
            and srt_path.is_file()
            and _is_newer_than_all(vtt_path, [clip_path])
            and _is_newer_than_all(srt_path, [clip_path])
        ):
            scene_vtt_paths.append(str(vtt_path))
            scene_srt_paths.append(str(srt_path))
            continue

        vtt_path.write_text(render_vtt(cues), encoding="utf-8")
        srt_path.write_text(render_srt(cues), encoding="utf-8")
        scene_vtt_paths.append(str(vtt_path))
        scene_srt_paths.append(str(srt_path))

    _emit_stage(job_id, "subtitle_gen.scenes", "stage_exit", ok=True)

    final_vtt_path: Path | None = None
    final_srt_path: Path | None = None
    if options.emit_job_final:
        _emit_stage(job_id, "subtitle_gen.final", "stage_enter")
        final_vtt_path = job_path / "final.vtt"
        final_srt_path = job_path / "final.srt"
        clip_paths = [scene_dir / "audio" / "clip.json" for scene_dir in scene_dirs]
        if (
            options.force
            or not final_vtt_path.is_file()
            or not final_srt_path.is_file()
            or not _is_newer_than_all(final_vtt_path, clip_paths)
            or not _is_newer_than_all(final_srt_path, clip_paths)
        ):
            final_cues = build_final_cues(scene_cues)
            final_vtt_path.write_text(render_vtt(final_cues), encoding="utf-8")
            final_srt_path.write_text(render_srt(final_cues), encoding="utf-8")
        _emit_stage(job_id, "subtitle_gen.final", "stage_exit", ok=True)

    return SubtitleResult(
        ok=True,
        scene_vtt_paths=scene_vtt_paths,
        scene_srt_paths=scene_srt_paths,
        final_vtt_path=str(final_vtt_path) if final_vtt_path else None,
        final_srt_path=str(final_srt_path) if final_srt_path else None,
    )


def build_final_cues(
    scene_cues: list[tuple[str, AudioClip, list[SubtitleCue]]],
) -> list[SubtitleCue]:
    final_cues: list[SubtitleCue] = []
    offset = 0.0
    for _scene_id, clip, cues in sorted(scene_cues, key=lambda item: item[0]):
        for cue in cues:
            final_cues.append(
                SubtitleCue(
                    start_seconds=cue.start_seconds + offset,
                    end_seconds=cue.end_seconds + offset,
                    text=cue.text,
                )
            )
        offset += clip.total_duration_seconds
    return final_cues


def render_vtt(cues: list[SubtitleCue]) -> str:
    blocks = ["WEBVTT", ""]
    for cue in cues:
        blocks.append(
            f"{format_vtt_time(cue.start_seconds)} --> {format_vtt_time(cue.end_seconds)}"
        )
        blocks.append(cue.text)
        blocks.append("")
    return "\n".join(blocks)


def render_srt(cues: list[SubtitleCue]) -> str:
    blocks: list[str] = []
    for index, cue in enumerate(cues, start=1):
        blocks.append(str(index))
        blocks.append(
            f"{format_srt_time(cue.start_seconds)} --> {format_srt_time(cue.end_seconds)}"
        )
        blocks.append(cue.text)
        blocks.append("")
    return "\n".join(blocks)


def _format_time(seconds: float, *, separator: str) -> str:
    total_ms = max(0, round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def _should_start_new_cue(
    current: list[WordTiming],
    word: WordTiming,
    char_budget: int,
    max_cue_seconds: float,
) -> bool:
    current_text = " ".join(item.word for item in current)
    candidate_len = len(current_text) + 1 + len(word.word)
    candidate_duration = word.end_seconds - current[0].start_seconds
    return (
        candidate_len > char_budget
        or candidate_duration > max_cue_seconds
        or current[-1].word.rstrip().endswith((".", "!", "?"))
    )


def _cue_from_words(
    words: list[WordTiming],
    max_chars_per_line: int,
    max_lines_per_cue: int,
) -> SubtitleCue:
    text = _wrap_text(" ".join(word.word for word in words), max_chars_per_line, max_lines_per_cue)
    return SubtitleCue(
        start_seconds=words[0].start_seconds,
        end_seconds=words[-1].end_seconds,
        text=text,
    )


def _coalesce_short_cues(
    cues: list[SubtitleCue],
    min_cue_seconds: float,
    max_chars_per_line: int,
    max_lines_per_cue: int,
) -> list[SubtitleCue]:
    out: list[SubtitleCue] = []
    for cue in cues:
        if out and cue.end_seconds - cue.start_seconds < min_cue_seconds:
            previous = out[-1]
            previous.end_seconds = cue.end_seconds
            previous.text = _wrap_text(
                f"{previous.text.replace(chr(10), ' ')} {cue.text.replace(chr(10), ' ')}",
                max_chars_per_line,
                max_lines_per_cue,
            )
        else:
            out.append(cue)
    return out


def _wrap_text(text: str, max_chars_per_line: int, max_lines_per_cue: int) -> str:
    lines = textwrap.wrap(
        text,
        width=max_chars_per_line,
        break_long_words=False,
        break_on_hyphens=False,
    )
    if len(lines) <= max_lines_per_cue:
        return "\n".join(lines)

    kept = lines[: max_lines_per_cue - 1]
    kept.append(" ".join(lines[max_lines_per_cue - 1 :]))
    return "\n".join(kept)


def _extend_last_cue_to_duration(cues: list[SubtitleCue], total_duration_seconds: float) -> None:
    if cues:
        cues[-1].end_seconds = total_duration_seconds


def _is_newer_than_all(target: Path, inputs: list[Path]) -> bool:
    target_mtime = target.stat().st_mtime
    return all(target_mtime >= input_path.stat().st_mtime for input_path in inputs)


def _emit_stage(job_id: str, stage: str, event: str, ok: bool | None = None) -> None:
    payload: dict[str, object] = {"event": event, "stage": stage, "producer": "subtitle-gen"}
    if ok is not None:
        payload["ok"] = ok
    try:
        append_event(job_id, json.dumps(payload))
    except (FileNotFoundError, ValueError):
        pass
