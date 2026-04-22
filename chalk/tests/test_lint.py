from pathlib import Path

from chalk.lint import lint_file, main


def _write_scene(path: Path, src: str) -> Path:
    path.write_text(src, encoding="utf-8")
    return path


def test_raw_hex_literal_reports_r1(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import MathTex, Scene

class Demo(Scene):
    def construct(self):
        MathTex("x", color="#ff0000")
""",
    )

    errors = lint_file(scene)

    assert len(errors) == 1
    assert errors[0].rule == "R1-raw-hex"


def test_numeric_scale_kwarg_reports_r2(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import MathTex, Scene

class Demo(Scene):
    def construct(self):
        MathTex("x", scale=0.37)
""",
    )

    errors = lint_file(scene)

    assert len(errors) == 1
    assert errors[0].rule == "R2-magic-scale"


def test_palette_constants_and_named_scales_pass(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import MathTex, PRIMARY, SCALE_BODY, Scene

class Demo(Scene):
    def construct(self):
        MathTex("x", color=PRIMARY, scale=SCALE_BODY)
""",
    )

    assert lint_file(scene) == []


def test_style_file_is_skipped_directly_and_by_cli():
    assert lint_file(Path("chalk/src/chalk/style.py")) == []
    assert main(["chalk-lint", "chalk/src/chalk/style.py"]) == 0


def test_motion_animation_between_clear_calls_passes_r3(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import ChangeValue, FadeIn, Scene

class Demo(Scene):
    def construct(self):
        self.play(ChangeValue(x, 1.0))
        self.clear()
        self.play(ChangeValue(y, 1.0))
        self.clear()
        self.play(FadeIn(y))
""",
    )

    assert [e.rule for e in lint_file(scene) if e.rule == "R3-no-motion"] == []


def test_fade_only_non_final_scene_reports_r3(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import FadeIn, Scene

class Demo(Scene):
    def construct(self):
        self.play(FadeIn(x))
        self.clear()
        self.play(FadeIn(y))
""",
    )

    errors = lint_file(scene)

    assert len(errors) == 1
    assert errors[0].rule == "R3-no-motion"


def test_four_self_play_calls_reports_r4(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import FadeIn, Scene

class Demo(Scene):
    def construct(self):
        self.play(FadeIn(a))
        self.play(FadeIn(b))
        self.play(FadeIn(c))
        self.play(FadeIn(d))
""",
    )

    errors = lint_file(scene)

    assert len(errors) == 1
    assert errors[0].rule == "R4-too-many-beats"


def test_three_self_play_calls_passes_r4(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import FadeIn, Scene

class Demo(Scene):
    def construct(self):
        self.play(FadeIn(a))
        self.play(FadeIn(b))
        self.play(FadeIn(c))
""",
    )

    assert [e.rule for e in lint_file(scene) if e.rule == "R4-too-many-beats"] == []


def test_hand_sized_rectangle_around_mathtex_reports_r5(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import FadeIn, MathTex, Rectangle, Scene, GREY, YELLOW, SCALE_LABEL

class Demo(Scene):
    def construct(self):
        box = Rectangle(width=2.0, height=1.4, color=GREY, stroke_width=1.5)
        box.shift(3.8, 0.0)
        lbl = MathTex(r"I = 2", color=YELLOW, scale=SCALE_LABEL)
        lbl.move_to(3.8, 0.0)
        self.add(box, lbl)
        self.play(FadeIn(box))
""",
    )

    errors = [e for e in lint_file(scene) if e.rule == "R5-hand-sized-box"]

    assert len(errors) == 1


def test_labeled_box_passes_r5(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import FadeIn, Scene, GREY, YELLOW, SCALE_LABEL, labeled_box

class Demo(Scene):
    def construct(self):
        box, lbl = labeled_box(r"I = 2", color=GREY, label_color=YELLOW, scale=SCALE_LABEL)
        box.shift(3.8, 0.0)
        lbl.move_to(3.8, 0.0)
        self.add(box, lbl)
        self.play(FadeIn(box))
""",
    )

    assert [e.rule for e in lint_file(scene) if e.rule == "R5-hand-sized-box"] == []


def test_long_static_beat_reports_r6(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import FadeIn, Scene

class Demo(Scene):
    def construct(self):
        self.play(FadeIn(a, run_time=0.5))
        self.wait(15.0)
""",
    )

    errors = [e for e in lint_file(scene) if e.rule == "R6-long-beat"]

    assert len(errors) == 1


def test_split_beats_pass_r6(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import FadeIn, ShiftAnim, Scene

class Demo(Scene):
    def construct(self):
        self.play(FadeIn(a, run_time=0.5))
        self.play(ShiftAnim(a, dx=1.0, dy=0.0, run_time=1.0))
        self.wait(6.0)
        self.clear()
        self.play(FadeIn(b, run_time=0.5))
        self.wait(5.0)
""",
    )

    assert [e.rule for e in lint_file(scene) if e.rule == "R6-long-beat"] == []


def test_rectangle_and_mathtex_at_different_coords_passes_r5(tmp_path: Path):
    scene = _write_scene(
        tmp_path / "scene.py",
        """\
from chalk import FadeIn, MathTex, Rectangle, Scene, GREY, PRIMARY, SCALE_BODY

class Demo(Scene):
    def construct(self):
        bg = Rectangle(width=10.0, height=6.0, color=GREY, fill_opacity=0.8)
        bg.shift(0.0, 0.0)
        title = MathTex(r"title", color=PRIMARY, scale=SCALE_BODY)
        title.move_to(0.0, 3.0)
        self.add(bg, title)
        self.play(FadeIn(bg))
""",
    )

    assert [e.rule for e in lint_file(scene) if e.rule == "R5-hand-sized-box"] == []
