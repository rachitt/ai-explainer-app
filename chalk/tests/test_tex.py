"""MathTex integration tests — require latex + dvisvgm on PATH."""
import pytest


def _has_latex() -> bool:
    import shutil, os
    env_path = "/Library/TeX/texbin" + os.pathsep + os.environ.get("PATH", "")
    return shutil.which("latex", path=env_path) is not None


pytestmark = pytest.mark.skipif(not _has_latex(), reason="latex not available")


def test_mathtex_returns_vgroup():
    from chalk.tex import MathTex
    from chalk.vgroup import VGroup
    m = MathTex(r"\frac{d}{dx} f(x)")
    assert isinstance(m, VGroup)
    assert len(m) > 0


def test_mathtex_submobjects_have_points():
    from chalk.tex import MathTex
    m = MathTex(r"x^2 + 1")
    for mob in m:
        assert len(mob.points) > 0
        assert len(mob.points) % 4 == 0


def test_mathtex_cache_hit(tmp_path, monkeypatch):
    from chalk import tex as tex_mod
    monkeypatch.setattr(tex_mod, "_CACHE_DIR", tmp_path)
    m1 = tex_mod.MathTex(r"e^{i\pi}")
    m2 = tex_mod.MathTex(r"e^{i\pi}")
    # Both produce same number of submobjects
    assert len(m1) == len(m2)


def test_mathtex_color_applied():
    from chalk.tex import MathTex
    m = MathTex(r"\alpha", color="#ff0000")
    for mob in m:
        assert mob.fill_color == "#ff0000"


def test_mathtex_scale():
    from chalk.tex import MathTex
    import numpy as np
    m1 = MathTex(r"\pi")
    m2 = MathTex(r"\pi", scale=2.0)
    # scaled version should span wider
    pts1 = np.concatenate([mob.points for mob in m1])
    pts2 = np.concatenate([mob.points for mob in m2])
    assert pts2[:, 0].max() - pts2[:, 0].min() > pts1[:, 0].max() - pts1[:, 0].min()
