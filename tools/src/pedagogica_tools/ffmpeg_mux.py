"""Mux per-scene chalk renders and narration with FFmpeg."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pedagogica_schemas.sync import SyncPlan
from pydantic import BaseModel, ValidationError

from pedagogica_tools._trace import append_event


@dataclass
class MuxOptions:
    crossfade_seconds: float = 0.0
    output_name: str = "final.mp4"
    force: bool = False
    scenes_only: bool = False
    concat_only: bool = False


class MuxResult(BaseModel):
    ok: bool
    output_path: str | None = None
    duration_seconds: float | None = None
    error: str | None = None


def build_concat_synced_content(scene_ids: list[str]) -> str:
    return "".join(f"file 'scenes/{scene_id}/synced.mp4'\n" for scene_id in sorted(scene_ids))


def mux(job_dir: str | Path, options: MuxOptions) -> MuxResult:
    if options.crossfade_seconds > 0:
        raise NotImplementedError("crossfade is a phase 2 feature; see docs/CHALK_ROADMAP.md")

    job_path = Path(job_dir).resolve()
    output_path = job_path / options.output_name
    job_id = job_path.name

    if not job_path.is_dir():
        return MuxResult(ok=False, error=f"job dir does not exist: {job_path}")

    scenes_root = job_path / "scenes"
    if not scenes_root.is_dir():
        return MuxResult(ok=False, error=f"scenes dir does not exist: {scenes_root}")

    env = _subprocess_env()
    ffmpeg = shutil.which("ffmpeg", path=env.get("PATH"))
    if ffmpeg is None:
        return MuxResult(ok=False, error="ffmpeg not found on PATH")

    scene_dirs = sorted(p for p in scenes_root.iterdir() if p.is_dir())
    if not scene_dirs:
        return MuxResult(ok=False, error=f"no scene dirs found: {scenes_root}")

    if not options.concat_only:
        result = _mux_scenes(job_id, scene_dirs, ffmpeg, env, options)
        if not result.ok:
            return result

    if options.scenes_only:
        return MuxResult(ok=True)

    return _concat(job_id, job_path, scene_dirs, output_path, ffmpeg, env, options)


def _mux_scenes(
    job_id: str,
    scene_dirs: list[Path],
    ffmpeg: str,
    env: dict[str, str],
    options: MuxOptions,
) -> MuxResult:
    _emit_stage(job_id, "ffmpeg_mux.scenes", "stage_enter")
    for scene_dir in scene_dirs:
        scene_id = scene_dir.name
        sync_path = scene_dir / "sync.json"
        audio_path = scene_dir / "audio" / "clip.mp3"
        synced_path = scene_dir / "synced.mp4"

        if not sync_path.is_file():
            _emit_stage(job_id, "ffmpeg_mux.scenes", "stage_exit", ok=False)
            return MuxResult(ok=False, error=f"missing sync.json: {sync_path}")
        if not audio_path.is_file():
            _emit_stage(job_id, "ffmpeg_mux.scenes", "stage_exit", ok=False)
            return MuxResult(ok=False, error=f"missing audio file: {audio_path}")

        try:
            sync_plan = SyncPlan.model_validate_json(sync_path.read_text(encoding="utf-8"))
        except (ValidationError, json.JSONDecodeError) as e:
            _emit_stage(job_id, "ffmpeg_mux.scenes", "stage_exit", ok=False)
            return MuxResult(ok=False, error=str(e))

        scene_video = _find_scene_video(scene_dir)
        if scene_video is None:
            _emit_stage(job_id, "ffmpeg_mux.scenes", "stage_exit", ok=False)
            return MuxResult(ok=False, error=f"missing source scene mp4 in {scene_dir}")

        if (
            not options.force
            and synced_path.is_file()
            and _is_newer_than_all(synced_path, [scene_video, audio_path])
        ):
            continue

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(scene_video),
            "-itsoffset",
            str(sync_plan.audio_offset_seconds),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-t",
            str(sync_plan.total_scene_duration),
            str(synced_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, env=env, text=True, check=False)
        if proc.returncode != 0:
            _emit_stage(job_id, "ffmpeg_mux.scenes", "stage_exit", ok=False)
            return MuxResult(ok=False, error=_ffmpeg_error(scene_id, proc))

    _emit_stage(job_id, "ffmpeg_mux.scenes", "stage_exit", ok=True)
    return MuxResult(ok=True)


def _concat(
    job_id: str,
    job_path: Path,
    scene_dirs: list[Path],
    output_path: Path,
    ffmpeg: str,
    env: dict[str, str],
    options: MuxOptions,
) -> MuxResult:
    _emit_stage(job_id, "ffmpeg_mux.concat", "stage_enter")
    synced_paths = [scene_dir / "synced.mp4" for scene_dir in scene_dirs]
    missing = [p for p in synced_paths if not p.is_file()]
    if missing:
        _emit_stage(job_id, "ffmpeg_mux.concat", "stage_exit", ok=False)
        return MuxResult(ok=False, error=f"missing synced scene mp4: {missing[0]}")

    concat_path = job_path / "concat_synced.txt"
    concat_path.write_text(
        build_concat_synced_content([scene_dir.name for scene_dir in scene_dirs]),
        encoding="utf-8",
    )

    if (
        not options.force
        and output_path.is_file()
        and _is_newer_than_all(output_path, synced_paths)
    ):
        _emit_stage(job_id, "ffmpeg_mux.concat", "stage_exit", ok=True)
        return MuxResult(
            ok=True,
            output_path=str(output_path),
            duration_seconds=_probe_duration(output_path, env),
        )

    # Re-encode audio at concat so that audio packet boundaries don't get dropped
    # at scene transitions (stream-copy concat occasionally loses the last
    # 50-100 ms of each segment's audio, which reads as a cut).
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "44100",
        str(output_path),
    ]
    proc = subprocess.run(cmd, cwd=job_path, capture_output=True, env=env, text=True, check=False)
    if proc.returncode != 0:
        _emit_stage(job_id, "ffmpeg_mux.concat", "stage_exit", ok=False)
        return MuxResult(
            ok=False,
            output_path=str(output_path),
            error=_ffmpeg_error("concat", proc),
        )

    _emit_stage(job_id, "ffmpeg_mux.concat", "stage_exit", ok=True)
    return MuxResult(
        ok=True,
        output_path=str(output_path),
        duration_seconds=_probe_duration(output_path, env),
    )


def _find_scene_video(scene_dir: Path) -> Path | None:
    candidates = sorted(
        p for p in scene_dir.glob("*.mp4") if p.name != "synced.mp4" and p.is_file()
    )
    if not candidates:
        return None
    preferred = scene_dir / f"{scene_dir.name}.mp4"
    if preferred in candidates:
        return preferred
    return candidates[0]


def _is_newer_than_all(target: Path, inputs: list[Path]) -> bool:
    target_mtime = target.stat().st_mtime
    return all(target_mtime >= input_path.stat().st_mtime for input_path in inputs)


def _probe_duration(path: Path, env: dict[str, str]) -> float | None:
    ffprobe = shutil.which("ffprobe", path=env.get("PATH"))
    if ffprobe is None:
        return None
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "quiet",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        env=env,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    path_parts = env.get("PATH", "").split(":") if env.get("PATH") else []
    for bin_dir in reversed(("/opt/homebrew/bin", "/usr/local/bin")):
        if bin_dir not in path_parts:
            path_parts.insert(0, bin_dir)
    env["PATH"] = ":".join(path_parts)
    return env


def _emit_stage(job_id: str, stage: str, event: str, ok: bool | None = None) -> None:
    payload: dict[str, object] = {"event": event, "stage": stage, "producer": "ffmpeg-mux"}
    if ok is not None:
        payload["ok"] = ok
    try:
        append_event(job_id, json.dumps(payload))
    except (FileNotFoundError, ValueError):
        pass


def _ffmpeg_error(label: str, proc: subprocess.CompletedProcess[str]) -> str:
    stderr = (proc.stderr or "").strip()
    tail = stderr[-4000:] if stderr else "(no stderr)"
    return f"ffmpeg failed for {label} with exit code {proc.returncode}: {tail}"
