"""Camera2D: maps world coordinates to pixel coordinates."""
from __future__ import annotations

import numpy as np


class Camera2D:
    """Orthographic 2D camera centered at origin."""

    def __init__(
        self,
        frame_width: float = 14.2,
        frame_height: float = 8.0,
        pixel_width: int = 1920,
        pixel_height: int = 1080,
        background_color: str = "#1a1a2e",
    ) -> None:
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        self.background_color = background_color

    def world_to_pixel(self, points: np.ndarray) -> np.ndarray:
        """Convert (N,2) world coords to (N,2) pixel coords (y flipped, origin top-left)."""
        px = (points[:, 0] / self.frame_width + 0.5) * self.pixel_width
        py = (0.5 - points[:, 1] / self.frame_height) * self.pixel_height
        return np.stack([px, py], axis=1)

    def hex_to_rgba(self, hex_color: str, opacity: float = 1.0) -> tuple[float, float, float, float]:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        return r, g, b, opacity
