"""Snapshot testing utilities for chalk scenes."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from chalk.scene import Scene

_SNAPSHOTS_DIR = Path(__file__).parent.parent.parent / "tests" / "snapshots"
_DIFFS_DIR = _SNAPSHOTS_DIR / "diffs"


class FrameCapture:
    """Sink that captures the frame at `target_frame_index` and stops."""

    def __init__(self, target_frame_index: int) -> None:
        self._target = target_frame_index
        self._current = 0
        self.captured: np.ndarray | None = None

    def write(self, frame: np.ndarray) -> None:
        if self._current == self._target and self.captured is None:
            self.captured = frame.copy()
        self._current += 1


def snapshot(
    scene_cls: "type[Scene]",
    at_second: float,
    width: int = 640,
    height: int = 360,
    fps: int = 30,
) -> np.ndarray:
    """Render a single frame at `at_second`; return RGBA ndarray (H, W, 4)."""
    from chalk.camera import Camera2D
    from chalk.scene import Scene

    target_frame = max(0, round(at_second * fps))
    capture = FrameCapture(target_frame)

    scene = scene_cls()
    cam = Camera2D()
    cam.pixel_width = width
    cam.pixel_height = height
    scene._attach(capture, camera=cam, fps=fps)
    scene.construct()

    if capture.captured is None:
        # Scene shorter than at_second: return last rendered frame (re-render)
        if capture._current > 0:
            # Re-render the last frame via a fresh scene
            last_frame_idx = max(0, capture._current - 1)
            capture2 = FrameCapture(last_frame_idx)
            scene2 = scene_cls()
            scene2._attach(capture2, camera=cam, fps=fps)
            scene2.construct()
            return capture2.captured if capture2.captured is not None else np.zeros((height, width, 4), dtype=np.uint8)
        return np.zeros((height, width, 4), dtype=np.uint8)
    return capture.captured


def assert_snapshot(
    scene_cls: "type[Scene]",
    at_second: float,
    snapshot_name: str,
    update: bool = False,
    width: int = 640,
    height: int = 360,
    fps: int = 30,
) -> None:
    """Render a frame and compare to a saved baseline PNG.

    First call with `update=True` (or env var `UPDATE_SNAPSHOTS=1`) writes baseline.
    Subsequent calls compare byte-identically.  On mismatch, writes a diff image
    to tests/snapshots/diffs/<name>_diff.png.
    """
    import png  # type: ignore[import]

    _SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    do_update = update or os.environ.get("UPDATE_SNAPSHOTS", "") == "1"
    snap_file = _SNAPSHOTS_DIR / f"{snapshot_name}.png"

    frame = snapshot(scene_cls, at_second, width=width, height=height, fps=fps)
    h, w, _ = frame.shape

    if do_update or not snap_file.exists():
        _write_png(snap_file, frame)
        return

    baseline = _read_png(snap_file)
    if baseline.shape != frame.shape or not np.array_equal(baseline, frame):
        _DIFFS_DIR.mkdir(parents=True, exist_ok=True)
        diff_file = _DIFFS_DIR / f"{snapshot_name}_diff.png"
        _write_diff_png(diff_file, baseline, frame)
        raise AssertionError(
            f"Snapshot mismatch for '{snapshot_name}' at t={at_second}s. "
            f"Diff written to {diff_file}"
        )


def _write_png(path: Path, frame: np.ndarray) -> None:
    """Write RGBA ndarray as PNG using the pure-python `png` package."""
    import png
    h, w, _ = frame.shape
    # Flatten each row to width*4 values; greyscale=False → RGB/RGBA, not greyscale+alpha
    rows = [frame[y].flatten().tolist() for y in range(h)]
    with open(path, "wb") as f:
        writer = png.Writer(width=w, height=h, alpha=True, bitdepth=8, greyscale=False)
        writer.write(f, rows)


def _read_png(path: Path) -> np.ndarray:
    """Read a PNG file back as an RGBA ndarray."""
    import png
    reader = png.Reader(filename=str(path))
    w, h, rows, info = reader.read()
    channels = 4 if info.get("alpha") else 3
    data = np.array([list(r) for r in rows], dtype=np.uint8)
    return data.reshape(h, w, channels)


def _write_diff_png(path: Path, baseline: np.ndarray, actual: np.ndarray) -> None:
    """Write a diff image highlighting per-pixel differences."""
    import png
    try:
        h = max(baseline.shape[0], actual.shape[0])
        w = max(baseline.shape[1], actual.shape[1])
        base_pad = np.zeros((h, w, 4), dtype=np.uint8)
        act_pad = np.zeros((h, w, 4), dtype=np.uint8)
        bh, bw = min(baseline.shape[0], h), min(baseline.shape[1], w)
        ah, aw = min(actual.shape[0], h), min(actual.shape[1], w)
        base_pad[:bh, :bw] = baseline[:bh, :bw]
        act_pad[:ah, :aw] = actual[:ah, :aw]
        diff = np.abs(base_pad.astype(int) - act_pad.astype(int)).astype(np.uint8)
        diff[:, :, 3] = 255  # full alpha
        _write_png(path, diff)
    except Exception:
        pass  # best-effort diff
