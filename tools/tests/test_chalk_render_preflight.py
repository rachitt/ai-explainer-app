from pathlib import Path

from pedagogica_tools import chalk_render
from pedagogica_tools.chalk_render import RenderOptions, render


def test_chalk_render_returns_layout_overlap_on_preflight_failure(
    tmp_path: Path, monkeypatch
):
    code_path = tmp_path / "scene.py"
    code_path.write_text("class Bad: pass\n", encoding="utf-8")
    profile = tmp_path / "chalk.sb"
    profile.write_text("(version 1)\n", encoding="utf-8")
    chalk_bin = tmp_path / "chalk"
    chalk_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    output_path = tmp_path / "out.mp4"

    calls = []

    class FakePopen:
        returncode = 1
        pid = 12345

        def __init__(self, cmd, **kwargs):
            calls.append(cmd)

        def communicate(self, timeout=None):
            return (
                "",
                "preflight overlap: section=panels pair=0:<A>-1:<B> rect=(0, 0, 1, 1)",
            )

    monkeypatch.setattr(chalk_render, "_CHALK_BIN", chalk_bin)
    monkeypatch.setattr(chalk_render.subprocess, "Popen", FakePopen)

    result = render(
        code_path=code_path,
        scene_class="BadScene",
        output_path=output_path,
        scene_id="scene_bad",
        options=RenderOptions(sandbox_profile=profile),
    )

    assert result.success is False
    assert result.error_classification == "layout_overlap"
    assert result.stdout_tail is None
    assert result.video_path is None
    assert result.stderr is not None
    assert "preflight overlap" in result.stderr
    assert len(calls) == 1
    assert "--preflight" in calls[0]
    assert not output_path.exists()
