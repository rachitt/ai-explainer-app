"""Scene: orchestrates animations, drives the frame loop."""
from __future__ import annotations

from typing import TYPE_CHECKING

from chalk.camera import Camera2D, CameraFrame
from chalk.mobject import VMobject
from chalk.renderer import CairoRenderer
from chalk.vgroup import VGroup

if TYPE_CHECKING:
    from chalk.animation import Animation
    from chalk.output import FrameSink
    from chalk.redraw import AlwaysRedraw


class Scene:
    camera: Camera2D = Camera2D()
    fps: int = 30

    def __init__(self) -> None:
        self._mobjects: list[VMobject] = []
        self._redrawables: list["AlwaysRedraw"] = []
        self._sink: FrameSink | None = None
        self._renderer = CairoRenderer()
        self._frame_index: int = 0
        self._sections: list[tuple[str, int]] = []
        self._rendering_active: bool = True

    def _attach(self, sink: "FrameSink", camera: Camera2D | None = None, fps: int | None = None) -> None:
        self._sink = sink
        if camera is not None:
            self.camera = camera
        if fps is not None:
            self.fps = fps
        self._renderer.begin_scene(self.camera)

    def _flatten(self, m: VMobject | VGroup) -> list[VMobject]:
        """Recursively expand a VGroup tree into its leaf VMobjects."""
        if isinstance(m, VGroup):
            out: list[VMobject] = []
            for sub in m.submobjects:
                out.extend(self._flatten(sub))
            return out
        return [m]

    def _is_redrawable(self, m: VMobject | VGroup) -> bool:
        from chalk.redraw import AlwaysRedraw
        return isinstance(m, AlwaysRedraw)

    def _refresh_all(self) -> None:
        for rd in self._redrawables:
            rd.refresh()

    def _render_mobs(self) -> list[VMobject]:
        from chalk.animation import _iter_vmobjects
        mobs: list[VMobject] = list(self._mobjects)
        for rd in self._redrawables:
            mobs.extend(_iter_vmobjects(rd))
        return mobs

    def add(self, *mobjects: VMobject | VGroup) -> None:
        for m in mobjects:
            if self._is_redrawable(m):
                from chalk.redraw import AlwaysRedraw
                rd = m  # type: ignore[assignment]
                if rd not in self._redrawables:
                    self._redrawables.append(rd)  # type: ignore[arg-type]
            else:
                for leaf in self._flatten(m):
                    if leaf not in self._mobjects:
                        self._mobjects.append(leaf)

    def remove(self, *mobjects: VMobject | VGroup) -> None:
        for m in mobjects:
            if self._is_redrawable(m):
                if m in self._redrawables:
                    self._redrawables.remove(m)  # type: ignore[arg-type]
            else:
                for leaf in self._flatten(m):
                    if leaf in self._mobjects:
                        self._mobjects.remove(leaf)

    def play(self, *animations: "Animation", run_time: float | None = None) -> None:
        assert self._sink is not None, "scene not attached to a sink"
        for anim in animations:
            anim.begin()

        # Collect extra mobs spawned by animations (e.g. unmatched target glyphs
        # in TransformMatchingTex) that aren't yet in _mobjects.
        scene_ids = {id(m) for m in self._mobjects}
        extra: list[VMobject] = []
        for anim in animations:
            for m in getattr(anim, "_new_mobs", []):
                if id(m) not in scene_ids:
                    extra.append(m)
                    scene_ids.add(id(m))

        if not self._rendering_active:
            # Fast-forward: update state to end without writing any frames.
            for anim in animations:
                anim.interpolate(1.0)
                anim.finish()
            self._refresh_all()
            for m in extra:
                if m not in self._mobjects:
                    self._mobjects.append(m)
            return

        total_time = run_time or max(a.run_time for a in animations)
        n_frames = max(1, round(total_time * self.fps))

        for i in range(n_frames):
            alpha = i / (n_frames - 1) if n_frames > 1 else 1.0
            for anim in animations:
                anim_alpha = min(alpha * total_time / anim.run_time, 1.0)
                anim.interpolate(anim_alpha)
            self._refresh_all()
            frame = self._renderer.render_frame(self._render_mobs() + extra)
            self._sink.write(frame)
            self._frame_index += 1

        for anim in animations:
            anim.finish()

        # Persist extra mobs into the scene so they survive subsequent wait() calls.
        for m in extra:
            if m not in self._mobjects:
                self._mobjects.append(m)

    def wait(self, duration: float = 1.0) -> None:
        assert self._sink is not None, "scene not attached to a sink"
        if not self._rendering_active:
            self._refresh_all()
            return
        n_frames = max(1, round(duration * self.fps))
        for _ in range(n_frames):
            self._refresh_all()
            frame = self._renderer.render_frame(self._render_mobs())
            self._sink.write(frame)
            self._frame_index += 1

    def next_section(self, name: str = "", skip_animations: bool = False) -> None:
        """Begin a new named section. skip_animations=True fast-forwards play/wait (no frames written)."""
        self._sections.append((name, self._frame_index))
        self._rendering_active = not skip_animations

    def save_last_frame(self, path: str) -> None:
        """Render the current scene state and write it as a PNG to path."""
        import png  # type: ignore[import]
        frame = self._renderer.render_frame(self._render_mobs())
        h, w, _ = frame.shape
        rows = [frame[y].flatten().tolist() for y in range(h)]
        with open(path, "wb") as f:
            writer = png.Writer(width=w, height=h, alpha=True, bitdepth=8, greyscale=False)
            writer.write(f, rows)

    @property
    def camera_frame(self) -> CameraFrame:
        """Proxy for animating camera pan and zoom via CameraShift / CameraZoom."""
        return CameraFrame(self.camera)

    def clear(self, run_time: float = 0.5, keep: list | None = None) -> None:
        """Fade out every currently-added mobject (except those in `keep`) and
        remove them from the scene.  Use this between beats so elements don't
        pile up across acts.

        `keep` may contain VMobjects and/or VGroups.  For a VGroup, all of its
        submobjects are preserved — matching the Scene.add()/remove() semantics
        that expand VGroups into their constituent VMobjects on insertion.
        """
        from chalk.animation import FadeOut, _iter_vmobjects
        keep_ids: set[int] = set()
        for k in (keep or []):
            for leaf in self._flatten(k):
                keep_ids.add(id(leaf))
        keep_rd_ids = {id(k) for k in (keep or [])}

        if not self._rendering_active:
            # Fast-forward: drop mobs without rendering a fade.
            self._mobjects = [m for m in self._mobjects if id(m) in keep_ids]
            self._redrawables = [rd for rd in self._redrawables if id(rd) in keep_rd_ids]
            return

        to_fade = [m for m in self._mobjects if id(m) not in keep_ids]
        # Also fade current leaves from redrawables (excluding kept redrawables)
        for rd in self._redrawables:
            if id(rd) not in keep_rd_ids:
                to_fade.extend(_iter_vmobjects(rd))
        if not to_fade:
            # Still drop redrawables that aren't kept
            self._redrawables = [rd for rd in self._redrawables
                                  if id(rd) in keep_rd_ids]
            return
        self.play(*[FadeOut(m, run_time=run_time) for m in to_fade],
                  run_time=run_time)
        for m in to_fade:
            if m in self._mobjects:
                self._mobjects.remove(m)
        self._redrawables = [rd for rd in self._redrawables
                             if id(rd) in keep_rd_ids]

    def section(self, name: str) -> None:
        """Mark the current timeline position with a named bookmark."""
        self._sections.append((name, self._frame_index))

    @property
    def sections(self) -> list[tuple[str, int]]:
        """List of (name, frame_index) pairs emitted so far."""
        return list(self._sections)

    def construct(self) -> None:
        """Override in subclasses to define the animation."""
        pass
