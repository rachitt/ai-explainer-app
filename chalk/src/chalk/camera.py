"""Camera2D: maps world coordinates to pixel coordinates."""
from __future__ import annotations

import os

import numpy as np


class Camera2D:
    """Orthographic 2D camera with pan and zoom."""

    def __init__(
        self,
        frame_width: float = 14.2,
        frame_height: float = 8.0,
        pixel_width: int = 1920,
        pixel_height: int = 1080,
        background_color: str | None = None,
    ) -> None:
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        # Chalkboard aesthetic: when CHALK_STYLE=chalkboard, swap in the
        # slate chalkboard background unless the caller passed an explicit
        # override. This is half of chalk's visual identity (the other
        # half is seeded stroke jitter in the renderer).
        if background_color is None:
            if os.environ.get("CHALK_STYLE", "").lower() == "chalkboard":
                background_color = "#2E3B36"  # BG_CHALKBOARD (slate)
            else:
                background_color = "#0E1116"
        self.background_color = background_color
        self.center_x: float = 0.0
        self.center_y: float = 0.0
        self.zoom: float = 1.0

    def world_to_pixel(self, points: np.ndarray) -> np.ndarray:
        """Convert (N,2) world coords to (N,2) pixel coords, accounting for pan and zoom."""
        centered = (points - np.array([self.center_x, self.center_y])) * self.zoom
        px = (centered[:, 0] / self.frame_width + 0.5) * self.pixel_width
        py = (0.5 - centered[:, 1] / self.frame_height) * self.pixel_height
        return np.stack([px, py], axis=1)

    def hex_to_rgba(self, hex_color: str, opacity: float = 1.0) -> tuple[float, float, float, float]:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        return r, g, b, opacity


class CameraFrame:
    """Proxy exposing camera pan/zoom for use in CameraShift/CameraZoom animations."""

    def __init__(self, camera: Camera2D) -> None:
        self._camera = camera

    @property
    def center_x(self) -> float:
        return self._camera.center_x

    @center_x.setter
    def center_x(self, v: float) -> None:
        self._camera.center_x = v

    @property
    def center_y(self) -> float:
        return self._camera.center_y

    @center_y.setter
    def center_y(self, v: float) -> None:
        self._camera.center_y = v

    @property
    def zoom(self) -> float:
        return self._camera.zoom

    @zoom.setter
    def zoom(self, v: float) -> None:
        self._camera.zoom = v
