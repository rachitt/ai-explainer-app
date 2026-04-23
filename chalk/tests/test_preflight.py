from pathlib import Path

from typer.testing import CliRunner

from chalk.cli import app


def test_preflight_passing_scene(tmp_path: Path):
    scene_py = tmp_path / "passing.py"
    scene_py.write_text(
        """from chalk import Scene, Axes, MathTex, GREY, SCALE_ANNOT, ZONE_TOP, place_in_zone

class Passing(Scene):
    def construct(self):
        self.section("setup")
        ax = Axes(width=5.0, height=2.5, color=GREY)
        title = MathTex(r"\\text{Clean layout}", color=GREY, scale=SCALE_ANNOT)
        place_in_zone(title, ZONE_TOP)
        self.add(ax, title)
        self.wait(0.1)
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, [str(scene_py), "--scene", "Passing", "--preflight"])

    assert result.exit_code == 0, result.output
    assert "preflight ok:" in result.output


def test_preflight_fails_on_overlapping_panels(tmp_path: Path):
    scene_py = tmp_path / "overlap.py"
    scene_py.write_text(
        """from chalk import Scene, Rectangle, PRIMARY, BLUE

class Overlap(Scene):
    def construct(self):
        self.section("panels")
        a = Rectangle(width=3.0, height=2.0, color=PRIMARY)
        b = Rectangle(width=3.0, height=2.0, color=BLUE)
        b.shift(0.5, 0.0)
        self.add(a, b)
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, [str(scene_py), "--scene", "Overlap", "--preflight"])

    assert result.exit_code == 1
    assert "preflight overlap:" in result.output


def test_preflight_fails_on_off_frame_mathtex(tmp_path: Path):
    scene_py = tmp_path / "offframe.py"
    scene_py.write_text(
        """from chalk import Scene, MathTex, PRIMARY, SCALE_BODY

class OffFrame(Scene):
    def construct(self):
        self.section("bad")
        eq = MathTex(r"x^2", color=PRIMARY, scale=SCALE_BODY)
        eq.move_to(8.0, 0.0)
        self.add(eq)
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, [str(scene_py), "--scene", "OffFrame", "--preflight"])

    assert result.exit_code == 1
    assert "preflight offframe:" in result.output
