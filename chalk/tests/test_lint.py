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
