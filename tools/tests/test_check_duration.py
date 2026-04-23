from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from pedagogica_schemas.chalk_code import CompileResult
from pedagogica_tools.check_duration import (
    check_job_duration,
    format_report,
    load_latest_compile_result,
)
from pedagogica_tools.cli import app
from typer.testing import CliRunner


runner = CliRunner()


def _compile_result(
    scene_id: str,
    *,
    attempt_number: int = 1,
    video_duration_seconds: float | None,
    target_duration_seconds: float | None,
    frame_count: int | None = None,
    success: bool = True,
) -> CompileResult:
    return CompileResult(
        trace_id=uuid4(),
        span_id=uuid4(),
        producer="test",
        scene_id=scene_id,
        success=success,
        attempt_number=attempt_number,
        frame_count=frame_count,
        video_duration_seconds=video_duration_seconds,
        target_duration_seconds=target_duration_seconds,
    )


def _write_attempt(
    job_dir: Path,
    scene_id: str,
    *,
    attempt_number: int = 1,
    video_duration_seconds: float | None,
    target_duration_seconds: float | None,
    frame_count: int | None = None,
    success: bool = True,
) -> None:
    scene_dir = job_dir / "scenes" / scene_id
    scene_dir.mkdir(parents=True, exist_ok=True)
    result = _compile_result(
        scene_id,
        attempt_number=attempt_number,
        video_duration_seconds=video_duration_seconds,
        target_duration_seconds=target_duration_seconds,
        frame_count=frame_count,
        success=success,
    )
    (scene_dir / f"compile_attempt_{attempt_number}.json").write_text(
        result.model_dump_json(), encoding="utf-8"
    )


@pytest.fixture
def job_with_drift(tmp_path: Path) -> Path:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        video_duration_seconds=10.0,
        target_duration_seconds=10.2,
    )
    _write_attempt(
        job_dir,
        "scene_b",
        video_duration_seconds=8.0,
        target_duration_seconds=10.0,
    )
    return job_dir


def test_check_job_duration_computes_signed_drift(job_with_drift: Path) -> None:
    report = check_job_duration(job_with_drift, threshold=0.15)

    assert [scene.scene_id for scene in report.scenes] == ["scene_a", "scene_b"]
    scene_a, scene_b = report.scenes
    assert scene_a.drift_seconds == pytest.approx(-0.2)
    assert scene_a.drift_fraction == pytest.approx(-0.2 / 10.2)
    assert not scene_a.over_threshold
    assert scene_b.drift_seconds == pytest.approx(-2.0)
    assert scene_b.drift_fraction == pytest.approx(-0.2)
    assert scene_b.over_threshold
    assert report.any_over_threshold


def test_check_job_duration_threshold_controls_flag(job_with_drift: Path) -> None:
    report = check_job_duration(job_with_drift, threshold=0.25)

    assert not report.any_over_threshold
    assert not any(scene.over_threshold for scene in report.scenes)


def test_scene_without_compile_attempt_is_absent(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    (job_dir / "scenes" / "empty_scene").mkdir(parents=True)
    _write_attempt(
        job_dir,
        "scene_a",
        video_duration_seconds=10.0,
        target_duration_seconds=10.0,
    )

    report = check_job_duration(job_dir)

    assert [scene.scene_id for scene in report.scenes] == ["scene_a"]


def test_missing_duration_data_sets_missing_flag(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        video_duration_seconds=None,
        target_duration_seconds=10.0,
    )

    report = check_job_duration(job_dir)

    assert report.any_missing
    assert report.scenes[0].drift_seconds is None
    assert report.scenes[0].drift_fraction is None
    assert not report.scenes[0].over_threshold


def test_latest_compile_attempt_wins(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        attempt_number=1,
        video_duration_seconds=1.0,
        target_duration_seconds=10.0,
    )
    _write_attempt(
        job_dir,
        "scene_a",
        attempt_number=3,
        video_duration_seconds=10.0,
        target_duration_seconds=10.0,
    )

    result = load_latest_compile_result(job_dir / "scenes" / "scene_a")
    report = check_job_duration(job_dir, threshold=0.15)

    assert result is not None
    assert result.attempt_number == 3
    assert report.scenes[0].drift_fraction == pytest.approx(0.0)
    assert not report.any_over_threshold


def test_cli_non_strict_warns_and_strict_fails(job_with_drift: Path) -> None:
    non_strict = runner.invoke(app, ["check-duration", str(job_with_drift)])
    strict = runner.invoke(app, ["check-duration", str(job_with_drift), "--strict"])

    assert non_strict.exit_code == 0, non_strict.stderr
    assert "1/2 scenes over 15% drift; 0 missing duration data." in non_strict.stdout
    assert strict.exit_code == 1


def test_cli_missing_job_dir_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, ["check-duration", str(tmp_path / "missing")])

    assert result.exit_code == 2
    assert "not a directory" in result.stderr


def test_broken_render_detected_frame_count_zero(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        frame_count=0,
        video_duration_seconds=0.0,
        target_duration_seconds=10.0,
        success=True,
    )

    report = check_job_duration(job_dir)

    assert report.scenes[0].is_broken_render
    assert report.any_broken_render


def test_broken_render_detected_duration_zero_frames_nonzero(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        frame_count=5,
        video_duration_seconds=0.0,
        target_duration_seconds=10.0,
    )

    report = check_job_duration(job_dir)

    assert report.scenes[0].is_broken_render
    assert report.any_broken_render


def test_healthy_render_not_flagged_as_broken(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        frame_count=450,
        video_duration_seconds=15.0,
        target_duration_seconds=15.0,
    )

    report = check_job_duration(job_dir)

    assert not report.scenes[0].is_broken_render
    assert not report.any_broken_render


def test_failed_compile_not_flagged_as_broken(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        frame_count=0,
        video_duration_seconds=0.0,
        target_duration_seconds=10.0,
        success=False,
    )

    report = check_job_duration(job_dir)

    assert not report.scenes[0].is_broken_render
    assert not report.any_broken_render


def test_strict_flag_exits_1_on_broken_render(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        frame_count=0,
        video_duration_seconds=9.9,
        target_duration_seconds=10.0,
    )

    result = runner.invoke(app, ["check-duration", str(job_dir), "--strict"])

    assert result.exit_code == 1


def test_non_strict_exits_0_on_broken_render(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        frame_count=0,
        video_duration_seconds=9.9,
        target_duration_seconds=10.0,
    )

    result = runner.invoke(app, ["check-duration", str(job_dir)])

    assert result.exit_code == 0, result.stderr


def test_format_report_shows_broken_column(tmp_path: Path) -> None:
    job_dir = tmp_path / "job"
    _write_attempt(
        job_dir,
        "scene_a",
        frame_count=0,
        video_duration_seconds=9.9,
        target_duration_seconds=10.0,
    )

    output = format_report(check_job_duration(job_dir))

    assert "broken" in output
    assert "YES" in output
    assert "1 broken" in output
