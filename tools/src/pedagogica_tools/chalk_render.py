"""Sandbox + render a chalk scene.

Wraps the `chalk` CLI in `sandbox-exec -f sandbox/chalk.sb` with CPU / wall /
memory / output-size rlimits. Captures stderr, classifies failures into the
`ErrorClassification` enum, and returns a `CompileResult`.
See docs/ARCHITECTURE.md §5.7 and §9.
"""

from __future__ import annotations

import os
import re
import resource
import shutil
import signal
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from pedagogica_schemas.chalk_code import CompileResult, ErrorClassification

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SANDBOX_PROFILE = _REPO_ROOT / "sandbox" / "chalk.sb"
_CHALK_BIN = _REPO_ROOT / ".venv" / "bin" / "chalk"
SANDBOX_EXEC = "/usr/bin/sandbox-exec"

_STDERR_TAIL_BYTES = 16_000
_STDOUT_TAIL_LINES = 200

# 720p matches the Phase-1 quality target.
_DEFAULT_WIDTH = 1280
_DEFAULT_HEIGHT = 720


@dataclass
class RenderOptions:
    cpu_limit: int = 300
    wall_limit: int = 300
    memory_limit_mb: int = 4096
    output_size_limit_mb: int = 500
    width: int = _DEFAULT_WIDTH
    height: int = _DEFAULT_HEIGHT
    fps: int = 30
    sandbox_profile: Path | None = None
    extra_chalk_args: list[str] = field(default_factory=list)
    target_duration_seconds: float | None = None


_CLASSIFIERS: tuple[tuple[re.Pattern[str], ErrorClassification], ...] = (
    (
        re.compile(
            r"MemoryError|bad_alloc|Cannot allocate memory|Killed: 9|out of memory",
            re.IGNORECASE,
        ),
        "memory_error",
    ),
    (
        re.compile(r"ModuleNotFoundError|ImportError", re.IGNORECASE),
        "import_error",
    ),
    (
        re.compile(
            r"LaTeX Error|Emergency stop|latex\s*(compilation\s*)?failed|"
            r"pdflatex\b.*(fail|error)|Missing \\begin\{document\}|"
            r"! Undefined control sequence|"
            r"No such file or directory.*'(latex|xelatex|pdflatex)'|"
            r"FileNotFoundError.*'(latex|xelatex|pdflatex)'",
            re.IGNORECASE,
        ),
        "latex_error",
    ),
    (
        re.compile(
            r"got an unexpected keyword argument|"
            r"takes \d+ positional argument|"
            r"has no attribute|"
            r"object is not (callable|subscriptable|iterable)",
            re.IGNORECASE,
        ),
        "api_error",
    ),
    (
        re.compile(
            r"out of frame|zero width|zero height|"
            r"width.*must be positive|height.*must be positive",
            re.IGNORECASE,
        ),
        "geometry_error",
    ),
    (
        re.compile(
            r"SyntaxError|IndentationError|unexpected EOF",
            re.IGNORECASE,
        ),
        "syntax_error",
    ),
)


def classify_error(combined_output: str, *, timed_out: bool) -> ErrorClassification:
    if timed_out:
        return "timeout"
    for pattern, label in _CLASSIFIERS:
        if pattern.search(combined_output):
            return label
    return "other"


def _make_preexec(cpu_s: int, mem_mb: int, fsize_mb: int) -> Callable[[], None]:
    def _preexec() -> None:
        _try_setrlimit(resource.RLIMIT_CPU, cpu_s)
        mem_bytes = mem_mb * 1024 * 1024
        _try_setrlimit(resource.RLIMIT_AS, mem_bytes)
        _try_setrlimit(resource.RLIMIT_DATA, mem_bytes)
        _try_setrlimit(resource.RLIMIT_FSIZE, fsize_mb * 1024 * 1024)

    return _preexec


def _try_setrlimit(rlimit: int, value: int) -> None:
    try:
        resource.setrlimit(rlimit, (value, value))
    except (OSError, ValueError):
        pass


def _tail_bytes(s: str, n: int) -> str:
    encoded = s.encode("utf-8", errors="replace")
    if len(encoded) <= n:
        return s
    return encoded[-n:].decode("utf-8", errors="replace")


def _tail_lines(s: str, n: int) -> str:
    return "\n".join(s.splitlines()[-n:])


def _compile_result(
    *,
    scene_id: str,
    attempt_number: int,
    success: bool,
    video_path: str | None = None,
    frame_count: int | None = None,
    duration_seconds: float | None = None,
    video_duration_seconds: float | None = None,
    target_duration_seconds: float | None = None,
    stderr: str | None = None,
    stdout_tail: str | None = None,
    classification: ErrorClassification | None = None,
) -> CompileResult:
    return CompileResult(
        trace_id=uuid4(),
        span_id=uuid4(),
        producer="chalk-render",
        scene_id=scene_id,
        success=success,
        attempt_number=attempt_number,
        video_path=video_path,
        frame_count=frame_count,
        duration_seconds=duration_seconds,
        video_duration_seconds=video_duration_seconds,
        target_duration_seconds=target_duration_seconds,
        stderr=stderr,
        stdout_tail=stdout_tail,
        error_classification=classification,
    )


def _probe_video_duration(path: Path) -> float | None:
    """ffprobe the output mp4 for content duration. Returns None on any failure."""
    ffprobe = shutil.which("ffprobe")
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
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def _write_result(result: CompileResult, json_path: Path | str | None) -> CompileResult:
    if json_path is not None:
        p = Path(json_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(result.model_dump_json(indent=2))
    return result


def render(
    *,
    code_path: Path | str,
    scene_class: str,
    output_path: Path | str,
    scene_id: str,
    attempt_number: int = 1,
    options: RenderOptions | None = None,
    result_json_path: Path | str | None = None,
) -> CompileResult:
    """Render a chalk scene under sandbox-exec and return a CompileResult."""

    opts = options or RenderOptions()
    profile = Path(opts.sandbox_profile or DEFAULT_SANDBOX_PROFILE).resolve()
    code_path = Path(code_path).resolve()
    output_path = Path(output_path).resolve()
    chalk_bin = _CHALK_BIN if _CHALK_BIN.is_file() else shutil.which("chalk")

    if not profile.is_file():
        return _write_result(
            _compile_result(
                scene_id=scene_id,
                attempt_number=attempt_number,
                success=False,
                stderr=f"sandbox profile not found: {profile}",
                classification="other",
            ),
            result_json_path,
        )

    if not code_path.is_file():
        return _write_result(
            _compile_result(
                scene_id=scene_id,
                attempt_number=attempt_number,
                success=False,
                stderr=f"code path not found: {code_path}",
                classification="other",
            ),
            result_json_path,
        )

    if chalk_bin is None:
        return _write_result(
            _compile_result(
                scene_id=scene_id,
                attempt_number=attempt_number,
                success=False,
                stderr="chalk binary not found (expected .venv/bin/chalk)",
                classification="import_error",
            ),
            result_json_path,
        )

    artifact_dir = output_path.parent
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # TMPDIR inside artifact_dir so chalk_tex_cache and pdflatex temp files
    # land in the sandboxed write region.
    tmp_dir = artifact_dir / f"_chalk_tmp_{uuid4().hex[:8]}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        SANDBOX_EXEC,
        "-D",
        f"ARTIFACT_DIR={artifact_dir}",
        "-f",
        str(profile),
        str(chalk_bin),
        str(code_path),
        "-s", scene_class,
        "-o", str(output_path),
        "--width", str(opts.width),
        "--height", str(opts.height),
        "--fps", str(opts.fps),
        *opts.extra_chalk_args,
    ]

    env = os.environ.copy()
    env["TMPDIR"] = str(tmp_dir)
    tex_bin = "/Library/TeX/texbin"
    if tex_bin not in env.get("PATH", ""):
        env["PATH"] = tex_bin + ":" + env.get("PATH", "")

    start = time.monotonic()
    timed_out = False
    stdout = ""
    stderr = ""
    returncode = -1
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=_make_preexec(
                opts.cpu_limit, opts.memory_limit_mb, opts.output_size_limit_mb
            ),
            start_new_session=True,
            text=True,
        )
    except FileNotFoundError as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return _write_result(
            _compile_result(
                scene_id=scene_id,
                attempt_number=attempt_number,
                success=False,
                stderr=f"failed to invoke sandbox-exec: {e}",
                classification="other",
            ),
            result_json_path,
        )

    try:
        stdout, stderr = proc.communicate(timeout=opts.wall_limit)
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        returncode = proc.returncode

    elapsed = time.monotonic() - start
    stderr_tail = _tail_bytes(stderr or "", _STDERR_TAIL_BYTES)
    stdout_tail = _tail_lines(stdout or "", _STDOUT_TAIL_LINES)

    # chalk writes "Wrote <path>" to stdout on success with exit 0.
    success = returncode == 0 and not timed_out and output_path.is_file()
    video_path: str | None = None
    duration_seconds: float | None = None
    video_duration_seconds: float | None = None

    if success:
        video_path = str(output_path)
        duration_seconds = elapsed
        video_duration_seconds = _probe_video_duration(output_path)
    elif returncode == 0 and not output_path.is_file():
        success = False
        stderr_tail = (stderr_tail + "\n[exit 0 but no output file produced]").strip()

    classification: ErrorClassification | None = None
    if not success:
        classification = classify_error(
            (stderr_tail or "") + "\n" + (stdout_tail or ""), timed_out=timed_out
        )

    shutil.rmtree(tmp_dir, ignore_errors=True)

    return _write_result(
        _compile_result(
            scene_id=scene_id,
            attempt_number=attempt_number,
            success=success,
            video_path=video_path,
            duration_seconds=duration_seconds,
            video_duration_seconds=video_duration_seconds,
            target_duration_seconds=opts.target_duration_seconds,
            stderr=stderr_tail or None,
            stdout_tail=stdout_tail or None,
            classification=classification,
        ),
        result_json_path,
    )
