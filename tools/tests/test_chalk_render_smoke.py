'''Smoke test: chalk-render end-to-end. Skipped by default (slow + requires sandbox-exec + ffmpeg). Run with `uv run pytest tools/tests/test_chalk_render_smoke.py -m slow`.'''

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pedagogica_schemas.chalk_code import CompileResult


@pytest.mark.slow
@pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS sandbox-exec")
@pytest.mark.skipif(
    shutil.which("sandbox-exec") is None, reason="sandbox-exec not on PATH"
)
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")
def test_chalk_render_smoke(tmp_path: Path, request: pytest.FixtureRequest) -> None:
    if "slow" not in request.config.option.markexpr:
        pytest.skip("slow smoke test; run with -m slow")

    smoke_py = tmp_path / "smoke.py"
    out_mp4 = tmp_path / "out.mp4"
    result_json = tmp_path / "result.json"

    smoke_py.write_text(
        """from chalk import Scene, Circle, FadeIn, PRIMARY

class SmokeScene(Scene):
    def construct(self):
        c = Circle(radius=0.5, color=PRIMARY)
        self.add(c)
        self.play(FadeIn(c, run_time=0.3))
        self.wait(0.3)
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            "pedagogica-tools",
            "chalk-render",
            str(smoke_py),
            "SmokeScene",
            str(out_mp4),
            "--scene-id",
            "smoke_00",
            "--attempt",
            "1",
            "--result-json",
            str(result_json),
        ],
        timeout=90,
        check=False,
    )

    assert completed.returncode == 0
    assert out_mp4.exists()
    assert out_mp4.stat().st_size > 0
    assert result_json.exists()

    result = CompileResult.model_validate_json(result_json.read_text(encoding="utf-8"))
    assert result.success is True
    assert result.frame_count > 0
    assert result.video_duration_seconds > 0
