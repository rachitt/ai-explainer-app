"""FrameSink implementations: FFmpegSink, PreviewSink, TeeSink."""
from __future__ import annotations

import shutil
import subprocess
from typing import Protocol, Sequence

import numpy as np


class FrameSink(Protocol):
    def write(self, frame: np.ndarray) -> None: ...
    def close(self) -> None: ...


class FFmpegSink:
    """Pipe raw RGBA frames to ffmpeg, mux to MP4."""

    def __init__(self, output_path: str, fps: int, width: int, height: int) -> None:
        if shutil.which("ffmpeg") is None:
            raise RuntimeError(
                "ffmpeg not found on PATH. Install with: brew install ffmpeg"
            )
        self._proc = subprocess.Popen(
            [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-pix_fmt", "rgba",
                "-s", f"{width}x{height}",
                "-r", str(fps),
                "-i", "pipe:0",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def write(self, frame: np.ndarray) -> None:
        assert self._proc.stdin is not None
        self._proc.stdin.write(frame.tobytes())

    def close(self) -> None:
        assert self._proc.stdin is not None
        self._proc.stdin.close()
        self._proc.wait()


class PreviewSink:
    """Show frames in a pyglet window for live dev preview."""

    def __init__(self, width: int, height: int, title: str = "chalk") -> None:
        import pyglet
        self._width = width
        self._height = height
        self._window = pyglet.window.Window(width=width, height=height, caption=title)
        self._pyglet = pyglet

    def write(self, frame: np.ndarray) -> None:
        import pyglet
        # pyglet expects RGBA with origin at bottom-left; flip vertically
        flipped = np.flipud(frame).tobytes()
        img = pyglet.image.ImageData(self._width, self._height, "RGBA", flipped)
        self._window.clear()
        img.blit(0, 0)
        self._window.flip()
        self._pyglet.app.platform_event_loop.step(0)

    def close(self) -> None:
        self._window.close()


class TeeSink:
    """Forward frames to multiple sinks simultaneously."""

    def __init__(self, sinks: Sequence[FrameSink]) -> None:
        self._sinks = list(sinks)

    def write(self, frame: np.ndarray) -> None:
        for sink in self._sinks:
            sink.write(frame)

    def close(self) -> None:
        for sink in self._sinks:
            sink.close()
