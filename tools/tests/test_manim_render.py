"""Tests for pedagogica-tools manim-render.

Four cases exercised per ARCHITECTURE §9 + §5.7:
  1. passing minimal scene        (skipped if manim not installed)
  2. LaTeX error classified       (skipped if manim not installed)
  3. wall-clock timeout honored   (skipped if manim not installed)
  4. network-outbound denied by sandbox/manim.sb  (needs only sandbox-exec)

Plus a pure unit test for `classify_error` that needs nothing.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from pedagogica_tools.manim_render import (
    DEFAULT_SANDBOX_PROFILE,
    RenderOptions,
    classify_error,
    render,
)

HAS_MANIM = shutil.which("manim") is not None
HAS_SANDBOX = Path("/usr/bin/sandbox-exec").exists()

skip_if_no_manim = pytest.mark.skipif(
    not HAS_MANIM, reason="manim binary not installed on PATH"
)
skip_if_no_sandbox = pytest.mark.skipif(
    not HAS_SANDBOX, reason="sandbox-exec not available (non-macOS?)"
)


def test_classify_error_timeout_wins() -> None:
    assert classify_error("anything goes here", timed_out=True) == "timeout"


def test_classify_error_buckets() -> None:
    assert classify_error("ModuleNotFoundError: no module x", timed_out=False) == "import_error"
    assert classify_error("! LaTeX Error: Missing $ inserted", timed_out=False) == "latex_error"
    assert classify_error("run_time must be positive", timed_out=False) == "timing_error"
    assert (
        classify_error("MemoryError: out of memory during render", timed_out=False)
        == "memory_error"
    )
    assert classify_error("Mobject has no points", timed_out=False) == "geometry_error"
    assert classify_error("some unrelated traceback", timed_out=False) == "other"


@skip_if_no_sandbox
@skip_if_no_manim
def test_minimal_scene_renders(tmp_path: Path) -> None:
    code = tmp_path / "scene.py"
    code.write_text(
        textwrap.dedent(
            """
            from manim import Scene, Square

            class Minimal(Scene):
                def construct(self):
                    self.add(Square())
            """
        ).strip()
    )
    out = tmp_path / "out.mp4"
    result = render(
        code_path=code,
        scene_class="Minimal",
        output_path=out,
        scene_id="scene_min",
        options=RenderOptions(wall_limit=120),
    )
    assert result.success, f"render failed: {result.stderr!r}"
    assert result.video_path is not None
    assert Path(result.video_path).is_file()
    assert result.error_classification is None


@skip_if_no_sandbox
@skip_if_no_manim
def test_latex_error_is_classified(tmp_path: Path) -> None:
    code = tmp_path / "scene.py"
    # Unclosed brace in MathTex triggers a LaTeX compile failure.
    code.write_text(
        textwrap.dedent(
            r"""
            from manim import Scene, MathTex

            class BadLatex(Scene):
                def construct(self):
                    self.add(MathTex(r"\frac{1"))
            """
        ).strip()
    )
    out = tmp_path / "out.mp4"
    result = render(
        code_path=code,
        scene_class="BadLatex",
        output_path=out,
        scene_id="scene_latex",
        options=RenderOptions(wall_limit=120),
    )
    assert not result.success
    assert result.error_classification == "latex_error", (
        result.error_classification,
        result.stderr,
    )


@skip_if_no_sandbox
@skip_if_no_manim
def test_wall_clock_timeout(tmp_path: Path) -> None:
    code = tmp_path / "scene.py"
    code.write_text(
        textwrap.dedent(
            """
            import time
            from manim import Scene, Square

            class Slow(Scene):
                def construct(self):
                    time.sleep(60)
                    self.add(Square())
            """
        ).strip()
    )
    out = tmp_path / "out.mp4"
    result = render(
        code_path=code,
        scene_class="Slow",
        output_path=out,
        scene_id="scene_timeout",
        options=RenderOptions(wall_limit=3, cpu_limit=10),
    )
    assert not result.success
    assert result.error_classification == "timeout", (
        result.error_classification,
        result.stderr,
    )


@skip_if_no_sandbox
def test_profile_denies_outbound_network(tmp_path: Path) -> None:
    """Verify sandbox/manim.sb blocks a non-loopback TCP connect."""
    script = tmp_path / "probe.py"
    script.write_text(
        textwrap.dedent(
            """
            import socket, sys
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            try:
                s.connect(("93.184.216.34", 80))  # example.com
            except (PermissionError, OSError) as e:
                print(f"DENIED:{e}", file=sys.stderr)
                sys.exit(42)
            print("CONNECTED", file=sys.stderr)
            sys.exit(0)
            """
        ).strip()
    )
    proc = subprocess.run(
        [
            "/usr/bin/sandbox-exec",
            "-D",
            f"ARTIFACT_DIR={tmp_path}",
            "-f",
            str(DEFAULT_SANDBOX_PROFILE),
            sys.executable,
            str(script),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode != 0, f"expected sandbox deny, got exit 0; stderr={proc.stderr!r}"
    assert "CONNECTED" not in proc.stderr
    assert "DENIED" in proc.stderr or "not permitted" in proc.stderr.lower(), proc.stderr
