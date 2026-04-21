"""CLI smoke test: render demo scene to MP4, check file exists and has valid header."""
import os
import struct
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner


DEMO_SCENE = """\
from chalk import Scene, Circle, Square, Transform

class Demo(Scene):
    def construct(self):
        c = Circle(radius=1.0, color="#3498db")
        s = Square(side=2.0, color="#e74c3c")
        self.add(c)
        self.play(Transform(c, s), run_time=0.5)
        self.wait(0.1)
"""


@pytest.fixture
def demo_file(tmp_path: Path) -> Path:
    p = tmp_path / "demo.py"
    p.write_text(DEMO_SCENE)
    return p


def _has_ftyp_box(path: Path) -> bool:
    """Check MP4 ftyp box signature in first 12 bytes."""
    with open(path, "rb") as f:
        data = f.read(12)
    if len(data) < 8:
        return False
    return data[4:8] == b"ftyp"


def test_cli_render_to_mp4(demo_file: Path, tmp_path: Path):
    pytest.importorskip("shutil")
    import shutil
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not on PATH")

    from chalk.cli import app
    out = tmp_path / "out.mp4"
    runner = CliRunner()
    result = runner.invoke(app, ["render", str(demo_file), "--scene", "Demo", "-o", str(out), "--fps", "10"])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert out.stat().st_size > 0
    assert _has_ftyp_box(out)
