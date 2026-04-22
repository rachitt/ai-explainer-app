"""Tests for Scene.section() bookmarks and snapshot testing helper."""
import pytest
import numpy as np
from pathlib import Path

from chalk.scene import Scene
from chalk.shapes import Circle, Rectangle
from chalk.animation import FadeIn, FadeOut
from chalk.testing import snapshot, assert_snapshot


# ── Section bookmarks ───────────────────────────────────────────────────────

class _NullSink:
    def write(self, frame): pass


def _attach(scene):
    scene._attach(_NullSink())


class SectionScene(Scene):
    def construct(self):
        c = Circle(radius=0.5)
        self.add(c)
        self.play(FadeIn(c, run_time=1.0))  # 30 frames at fps=30
        self.wait(0.5)                       # 15 frames
        self.section("beat2")
        self.play(FadeOut(c, run_time=0.5))  # 15 frames


def test_section_records_name_and_frame():
    scene = SectionScene()
    _attach(scene)
    scene.construct()
    assert len(scene.sections) == 1
    name, frame_idx = scene.sections[0]
    assert name == "beat2"
    # After 30 (play) + 15 (wait) frames, beat2 is at frame 45
    assert frame_idx == 45


def test_section_no_sections_by_default():
    scene = Scene()
    _attach(scene)
    scene.construct()
    assert scene.sections == []


class TwoBeatScene(Scene):
    def construct(self):
        c = Circle(radius=0.5)
        self.add(c)
        self.play(FadeIn(c, run_time=1.0))
        self.section("beat1")
        self.wait(1.0)
        self.section("beat2")


def test_multiple_sections_ordering():
    scene = TwoBeatScene()
    _attach(scene)
    scene.construct()
    assert [s[0] for s in scene.sections] == ["beat1", "beat2"]
    assert scene.sections[0][1] < scene.sections[1][1]


# ── Snapshot helper ─────────────────────────────────────────────────────────

class SimpleColorScene(Scene):
    def construct(self):
        r = Rectangle(width=4.0, height=2.0, color="#4FC3F7", fill_color="#4FC3F7",
                      fill_opacity=1.0, stroke_width=0.0)
        self.add(r)
        self.play(FadeIn(r, run_time=1.0))
        self.wait(1.0)


def test_snapshot_returns_ndarray():
    frame = snapshot(SimpleColorScene, at_second=0.5, width=320, height=180, fps=30)
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (180, 320, 4)


def test_snapshot_nonzero_pixels():
    frame = snapshot(SimpleColorScene, at_second=1.5, width=320, height=180, fps=30)
    # Some pixels should be non-black (the blue rectangle)
    assert frame.sum() > 0


def test_assert_snapshot_write_and_match(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Redirect snapshot dir to tmp_path
    import chalk.testing as ct
    orig_dir = ct._SNAPSHOTS_DIR
    ct._SNAPSHOTS_DIR = tmp_path / "snapshots"
    ct._DIFFS_DIR = tmp_path / "snapshots" / "diffs"
    ct._SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Write baseline
        assert_snapshot(SimpleColorScene, 1.5, "simple_test", update=True,
                        width=160, height=90)
        snap_file = ct._SNAPSHOTS_DIR / "simple_test.png"
        assert snap_file.exists()

        # Compare — should pass
        assert_snapshot(SimpleColorScene, 1.5, "simple_test", update=False,
                        width=160, height=90)
    finally:
        ct._SNAPSHOTS_DIR = orig_dir
        ct._DIFFS_DIR = orig_dir / "diffs"


def test_assert_snapshot_mismatch_raises(tmp_path, monkeypatch):
    import chalk.testing as ct
    orig_dir = ct._SNAPSHOTS_DIR
    ct._SNAPSHOTS_DIR = tmp_path / "snapshots"
    ct._DIFFS_DIR = tmp_path / "snapshots" / "diffs"
    ct._SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Write baseline with SimpleColorScene
        assert_snapshot(SimpleColorScene, 1.5, "mismatch_test", update=True,
                        width=160, height=90)

        # Compare with a different scene — should fail
        class EmptyScene(Scene):
            def construct(self):
                self.wait(2.0)

        with pytest.raises(AssertionError, match="mismatch"):
            assert_snapshot(EmptyScene, 1.5, "mismatch_test", update=False,
                            width=160, height=90)
    finally:
        ct._SNAPSHOTS_DIR = orig_dir
        ct._DIFFS_DIR = orig_dir / "diffs"
