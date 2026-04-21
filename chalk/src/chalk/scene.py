"""Scene: orchestrates animations, drives the frame loop."""
from __future__ import annotations

from typing import TYPE_CHECKING

from chalk.camera import Camera2D
from chalk.mobject import VMobject
from chalk.renderer import CairoRenderer
from chalk.vgroup import VGroup

if TYPE_CHECKING:
    from chalk.animation import Animation
    from chalk.output import FrameSink


class Scene:
    camera: Camera2D = Camera2D()
    fps: int = 30

    def __init__(self) -> None:
        self._mobjects: list[VMobject] = []
        self._sink: FrameSink | None = None
        self._renderer = CairoRenderer()

    def _attach(self, sink: "FrameSink", camera: Camera2D | None = None, fps: int | None = None) -> None:
        self._sink = sink
        if camera is not None:
            self.camera = camera
        if fps is not None:
            self.fps = fps
        self._renderer.begin_scene(self.camera)

    def add(self, *mobjects: VMobject | VGroup) -> None:
        for m in mobjects:
            if isinstance(m, VGroup):
                for sub in m:
                    if sub not in self._mobjects:
                        self._mobjects.append(sub)
            elif m not in self._mobjects:
                self._mobjects.append(m)

    def remove(self, *mobjects: VMobject | VGroup) -> None:
        for m in mobjects:
            if isinstance(m, VGroup):
                for sub in m:
                    if sub in self._mobjects:
                        self._mobjects.remove(sub)
            elif m in self._mobjects:
                self._mobjects.remove(m)

    def play(self, *animations: "Animation", run_time: float | None = None) -> None:
        assert self._sink is not None, "scene not attached to a sink"
        for anim in animations:
            anim.begin()

        total_time = run_time or max(a.run_time for a in animations)
        n_frames = max(1, round(total_time * self.fps))

        for i in range(n_frames):
            alpha = i / (n_frames - 1) if n_frames > 1 else 1.0
            for anim in animations:
                anim_alpha = min(alpha * total_time / anim.run_time, 1.0)
                anim.interpolate(anim_alpha)
            frame = self._renderer.render_frame(self._mobjects)
            self._sink.write(frame)

        for anim in animations:
            anim.finish()

    def wait(self, duration: float = 1.0) -> None:
        assert self._sink is not None, "scene not attached to a sink"
        n_frames = max(1, round(duration * self.fps))
        for _ in range(n_frames):
            frame = self._renderer.render_frame(self._mobjects)
            self._sink.write(frame)

    def construct(self) -> None:
        """Override in subclasses to define the animation."""
        pass
