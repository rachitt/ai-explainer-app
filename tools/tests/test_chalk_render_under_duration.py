from __future__ import annotations

from pathlib import Path

from pedagogica_tools import chalk_render
from pedagogica_tools.chalk_render import RenderOptions, render


class _FakePopen:
    pid = 12345

    def __init__(self, cmd, **kwargs):
        self.cmd = cmd
        self.returncode = 0

    def communicate(self, timeout=None):
        if "--preflight" in self.cmd:
            return ("", "")
        output_index = self.cmd.index("-o") + 1
        Path(self.cmd[output_index]).write_bytes(b"fake mp4")
        return ("Wrote output\n", "")


def _setup_render_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    code_path = tmp_path / "scene.py"
    code_path.write_text("class Good: pass\n", encoding="utf-8")
    profile = tmp_path / "chalk.sb"
    profile.write_text("(version 1)\n", encoding="utf-8")
    chalk_bin = tmp_path / "chalk"
    chalk_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    return code_path, profile, chalk_bin


def test_under_duration_gate_rejects_short_render(tmp_path: Path, monkeypatch) -> None:
    code_path, profile, chalk_bin = _setup_render_inputs(tmp_path)
    output_path = tmp_path / "out.mp4"

    monkeypatch.setattr(chalk_render, "_CHALK_BIN", chalk_bin)
    monkeypatch.setattr(chalk_render.subprocess, "Popen", _FakePopen)
    monkeypatch.setattr(chalk_render, "_probe_video_duration", lambda path: 13.0)
    monkeypatch.setattr(chalk_render, "_probe_frame_count", lambda path: 390)

    result = render(
        code_path=code_path,
        scene_class="GoodScene",
        output_path=output_path,
        scene_id="scene_01",
        options=RenderOptions(sandbox_profile=profile, target_duration_seconds=50.0),
    )

    assert result.success is False
    assert result.error_classification == "under_duration"
    assert result.video_path == str(output_path)
    assert result.video_duration_seconds == 13.0
    assert result.frame_count == 390
    assert result.stderr is not None
    assert "[under_duration: video 13.00s < 0.85 × target 50.00s]" in result.stderr


def test_under_duration_gate_allows_near_target_render(
    tmp_path: Path, monkeypatch
) -> None:
    code_path, profile, chalk_bin = _setup_render_inputs(tmp_path)
    output_path = tmp_path / "out.mp4"

    monkeypatch.setattr(chalk_render, "_CHALK_BIN", chalk_bin)
    monkeypatch.setattr(chalk_render.subprocess, "Popen", _FakePopen)
    monkeypatch.setattr(chalk_render, "_probe_video_duration", lambda path: 48.0)
    monkeypatch.setattr(chalk_render, "_probe_frame_count", lambda path: 1440)

    result = render(
        code_path=code_path,
        scene_class="GoodScene",
        output_path=output_path,
        scene_id="scene_01",
        options=RenderOptions(sandbox_profile=profile, target_duration_seconds=50.0),
    )

    assert result.success is True
    assert result.error_classification is None
    assert result.video_duration_seconds == 48.0
    assert result.frame_count == 1440


def test_under_duration_gate_is_inactive_without_target(
    tmp_path: Path, monkeypatch
) -> None:
    code_path, profile, chalk_bin = _setup_render_inputs(tmp_path)
    output_path = tmp_path / "out.mp4"

    monkeypatch.setattr(chalk_render, "_CHALK_BIN", chalk_bin)
    monkeypatch.setattr(chalk_render.subprocess, "Popen", _FakePopen)
    monkeypatch.setattr(chalk_render, "_probe_video_duration", lambda path: 13.0)
    monkeypatch.setattr(chalk_render, "_probe_frame_count", lambda path: 390)

    result = render(
        code_path=code_path,
        scene_class="GoodScene",
        output_path=output_path,
        scene_id="scene_01",
        options=RenderOptions(sandbox_profile=profile),
    )

    assert result.success is True
    assert result.error_classification is None
    assert result.video_duration_seconds == 13.0
    assert result.frame_count == 390
