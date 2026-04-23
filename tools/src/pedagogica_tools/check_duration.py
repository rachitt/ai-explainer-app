from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pedagogica_schemas.chalk_code import CompileResult

_ATTEMPT_RE = re.compile(r"^compile_attempt_(\d+)\.json$")


@dataclass(frozen=True)
class SceneDurationDrift:
    scene_id: str
    video_duration_seconds: float | None
    target_duration_seconds: float | None
    drift_seconds: float | None
    drift_fraction: float | None
    over_threshold: bool
    frame_count: int | None = None
    success: bool = True

    @property
    def is_broken_render(self) -> bool:
        return self.success and (self.frame_count == 0 or self.video_duration_seconds == 0.0)


@dataclass(frozen=True)
class DurationReport:
    scenes: list[SceneDurationDrift]
    threshold: float
    any_missing: bool

    @property
    def any_over_threshold(self) -> bool:
        return any(s.over_threshold for s in self.scenes)

    @property
    def any_broken_render(self) -> bool:
        return any(s.is_broken_render for s in self.scenes)


def load_latest_compile_result(scene_dir: Path) -> CompileResult | None:
    latest: tuple[int, Path] | None = None
    for path in scene_dir.iterdir():
        match = _ATTEMPT_RE.match(path.name)
        if match is None:
            continue
        attempt_number = int(match.group(1))
        if latest is None or attempt_number > latest[0]:
            latest = (attempt_number, path)

    if latest is None:
        return None
    return CompileResult.model_validate_json(latest[1].read_text(encoding="utf-8"))


def check_job_duration(job_dir: Path, threshold: float = 0.15) -> DurationReport:
    scenes: list[SceneDurationDrift] = []
    any_missing = False
    scenes_dir = job_dir / "scenes"

    for scene_dir in sorted((p for p in scenes_dir.iterdir() if p.is_dir()), key=lambda p: p.name):
        result = load_latest_compile_result(scene_dir)
        if result is None:
            continue

        video = result.video_duration_seconds
        target = result.target_duration_seconds
        frame_count = result.frame_count
        success = result.success
        drift_seconds: float | None = None
        drift_fraction: float | None = None
        if video is None or target is None:
            any_missing = True
        else:
            drift_seconds = video - target
            drift_fraction = drift_seconds / target

        scenes.append(
            SceneDurationDrift(
                scene_id=scene_dir.name,
                video_duration_seconds=video,
                target_duration_seconds=target,
                drift_seconds=drift_seconds,
                drift_fraction=drift_fraction,
                over_threshold=drift_fraction is not None and abs(drift_fraction) > threshold,
                frame_count=frame_count,
                success=success,
            )
        )

    return DurationReport(scenes=scenes, threshold=threshold, any_missing=any_missing)


def _format_seconds(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def format_report(report: DurationReport) -> str:
    lines = [
        f"{'':1} {'scene_id':<20} {'video_s':>9} {'target_s':>9} {'drift_s':>9} "
        f"{'drift_%':>8} {'broken':>6}",
        "-" * 68,
    ]
    for scene in report.scenes:
        marker = "!" if scene.over_threshold or scene.is_broken_render else " "
        lines.append(
            f"{marker} {scene.scene_id:<20} "
            f"{_format_seconds(scene.video_duration_seconds):>9} "
            f"{_format_seconds(scene.target_duration_seconds):>9} "
            f"{_format_seconds(scene.drift_seconds):>9} "
            f"{_format_percent(scene.drift_fraction):>8} "
            f"{'YES' if scene.is_broken_render else '':>6}"
        )

    over_count = sum(1 for scene in report.scenes if scene.over_threshold)
    broken_count = sum(1 for scene in report.scenes if scene.is_broken_render)
    missing_count = sum(
        1
        for scene in report.scenes
        if scene.video_duration_seconds is None or scene.target_duration_seconds is None
    )
    summary = (
        f"{over_count}/{len(report.scenes)} scenes over {report.threshold * 100:g}% drift; "
        f"{missing_count} missing duration data."
    )
    if broken_count > 0:
        summary += f" {broken_count} broken renders."
    lines.append(summary)
    return "\n".join(lines)
