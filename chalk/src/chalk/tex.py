"""MathTex: render LaTeX math to a VGroup via latex → dvisvgm → SVG path parsing."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from chalk._svg import parse_svg_to_vmobjects
from chalk.vgroup import VGroup

_TEX_BIN = Path("/Library/TeX/texbin")

_TEX_TEMPLATE = r"""
\documentclass[preview,border=1pt]{standalone}
\usepackage{amsmath,amssymb}
\begin{document}
$\displaystyle %s $
\end{document}
"""

_CACHE_DIR = Path(tempfile.gettempdir()) / "chalk_tex_cache"


def _tex_env() -> dict[str, str]:
    env = os.environ.copy()
    tex_bin = str(_TEX_BIN)
    path = env.get("PATH", "")
    if tex_bin not in path:
        env["PATH"] = tex_bin + os.pathsep + path
    return env


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class MathTex(VGroup):
    """
    Render a LaTeX math string to a VGroup of VMobjects.

    Requires latex and dvisvgm in /Library/TeX/texbin (or on PATH).
    Results are cached by content hash under $TMPDIR/chalk_tex_cache/.
    """

    def __init__(
        self,
        tex_string: str,
        color: str = "#FFFFFF",
        stroke_width: float = 0.0,
        fill_opacity: float = 1.0,
        scale: float = 1.0,
    ) -> None:
        svg = _render_tex(tex_string)
        mobs = parse_svg_to_vmobjects(
            svg,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=color,
            fill_opacity=fill_opacity,
        )
        # Glyphs must not receive chalkboard-style jitter — LaTeX letters
        # rely on precise control points and even 0.015 world-unit noise
        # makes "V" read as "\" or gives characters ragged serifs.
        # Tag every glyph with a shared group id so preflight treats
        # intra-expression bbox nudges as non-overlaps — LaTeX places
        # adjacent letters within sub-pixel buffs by typesetting design.
        _group_id = id(self) & 0xFFFFFFFF
        for m in mobs:
            m._no_chalk_jitter = True  # type: ignore[attr-defined]
            m._tex_group_id = _group_id  # type: ignore[attr-defined]
        super().__init__(*mobs)
        if scale != 1.0:
            self.scale(scale)
        self.tex_string = tex_string


def _render_tex(tex_string: str) -> str:
    """Return SVG string for the given LaTeX math expression. Uses cache."""
    key = _content_hash(tex_string)
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _CACHE_DIR / f"{key}.svg"
    if cache_file.exists():
        return cache_file.read_text()

    svg = _compile_tex(tex_string)
    cache_file.write_text(svg)
    return svg


def _compile_tex(tex_string: str) -> str:
    """Run latex + dvisvgm in a temp dir, return SVG string."""
    _check_binaries()
    env = _tex_env()

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = Path(tmpdir) / "expr.tex"
        tex_file.write_text(_TEX_TEMPLATE % tex_string)

        # latex → dvi
        result = subprocess.run(
            ["latex", "-interaction=nonstopmode", "-halt-on-error", "expr.tex"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"latex failed for '{tex_string}':\n{result.stdout[-2000:]}"
            )

        dvi_file = Path(tmpdir) / "expr.dvi"
        if not dvi_file.exists():
            raise RuntimeError(f"latex produced no DVI for '{tex_string}'")

        # dvi → svg (no font embedding; use paths)
        result = subprocess.run(
            [
                "dvisvgm",
                "--no-fonts",
                "--exact",
                "--stdout",
                "expr.dvi",
            ],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"dvisvgm failed for '{tex_string}':\n{result.stderr[-2000:]}"
            )

        return result.stdout


def _check_binaries() -> None:
    env = _tex_env()
    path_dirs = env.get("PATH", "").split(os.pathsep)

    def find(name: str) -> bool:
        return shutil.which(name, path=env.get("PATH")) is not None

    missing = [b for b in ("latex", "dvisvgm") if not find(b)]
    if missing:
        raise RuntimeError(
            f"Missing binaries: {missing}. "
            "Install MacTeX: https://tug.org/mactex/ or ensure /Library/TeX/texbin is on PATH."
        )
