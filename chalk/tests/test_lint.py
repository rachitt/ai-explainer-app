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
