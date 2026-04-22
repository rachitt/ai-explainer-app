"""TransformMatchingTex: equation rearrangement via token-identity matching."""
from __future__ import annotations

import re
from typing import Callable

import numpy as np

from chalk.animation import FadeIn, FadeOut, Transform, _iter_vmobjects
from chalk.mobject import VMobject
from chalk.rate_funcs import smooth
from chalk.vgroup import VGroup


def _tokenize(tex: str) -> list[str]:
    """Split a LaTeX string into surface-level semantic atoms.

    Rules (no attempt at full LaTeX parsing):
    - Skip whitespace
    - \\name → one token (backslash + letters)
    - \\X    → two-char token for non-letter control sequences
    - { ... } → the whole group as one token
    - everything else → single character
    """
    tokens: list[str] = []
    i = 0
    while i < len(tex):
        c = tex[i]
        if c in " \t\n\r":
            i += 1
        elif c == "\\":
            j = i + 1
            if j < len(tex) and tex[j].isalpha():
                while j < len(tex) and tex[j].isalpha():
                    j += 1
            else:
                j += 1  # \X
            tokens.append(tex[i:j])
            i = j
        elif c == "{":
            depth, j = 1, i + 1
            while j < len(tex) and depth > 0:
                if tex[j] == "{":
                    depth += 1
                elif tex[j] == "}":
                    depth -= 1
                j += 1
            tokens.append(tex[i:j])
            i = j
        else:
            tokens.append(c)
            i += 1
    return tokens


def _greedy_match(
    src_tokens: list[str], tgt_tokens: list[str]
) -> tuple[list[tuple[int, int]], set[int], set[int]]:
    """Greedily match source tokens to target tokens (first-occurrence wins).

    Returns (matches, unmatched_src_indices, unmatched_tgt_indices).
    """
    matches: list[tuple[int, int]] = []
    used_src: set[int] = set()
    used_tgt: set[int] = set()

    for tgt_i, tok in enumerate(tgt_tokens):
        for src_i, src_tok in enumerate(src_tokens):
            if src_i not in used_src and src_tok == tok:
                matches.append((src_i, tgt_i))
                used_src.add(src_i)
                used_tgt.add(tgt_i)
                break

    unmatched_src = set(range(len(src_tokens))) - used_src
    unmatched_tgt = set(range(len(tgt_tokens))) - used_tgt
    return matches, unmatched_src, unmatched_tgt


class TransformMatchingTex:
    """Morph source MathTex into target MathTex by matching LaTeX tokens.

    Common tokens Transform between their respective glyph positions.
    Source-only tokens FadeOut; target-only tokens FadeIn from their positions.
    """

    def __init__(
        self,
        source: "VGroup",
        target: "VGroup",
        run_time: float = 1.5,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        self.source = source
        self.target = target
        self.run_time = run_time
        self.rate_func = rate_func
        self._inner: list = []
        self._new_mobs: list[VMobject] = []

    @property
    def mobjects(self) -> list[VMobject]:
        mobs = _iter_vmobjects(self.source)
        mobs.extend(self._new_mobs)
        return mobs

    def begin(self) -> None:
        from chalk.tex import MathTex
        src_tex = getattr(self.source, "tex_string", "")
        tgt_tex = getattr(self.target, "tex_string", "")

        src_tokens = _tokenize(src_tex)
        tgt_tokens = _tokenize(tgt_tex)

        src_glyphs = self.source.submobjects
        tgt_glyphs = self.target.submobjects

        # Clamp token lists to glyph count (approximate 1 token = 1 glyph)
        n_src = min(len(src_tokens), len(src_glyphs))
        n_tgt = min(len(tgt_tokens), len(tgt_glyphs))
        src_tokens = src_tokens[:n_src]
        tgt_tokens = tgt_tokens[:n_tgt]

        matches, unmatched_src, unmatched_tgt = _greedy_match(src_tokens, tgt_tokens)

        self._inner = []
        self._new_mobs = []

        # Matched pairs: Transform source glyph → target glyph geometry
        for src_i, tgt_i in matches:
            if src_i < len(src_glyphs) and tgt_i < len(tgt_glyphs):
                sg = src_glyphs[src_i]
                tg = tgt_glyphs[tgt_i]
                if isinstance(sg, VMobject) and isinstance(tg, VMobject):
                    anim = Transform(sg, tg, run_time=self.run_time,
                                     rate_func=self.rate_func)
                    self._inner.append(anim)

        # Unmatched source glyphs: FadeOut
        for src_i in sorted(unmatched_src):
            if src_i < len(src_glyphs):
                sg = src_glyphs[src_i]
                self._inner.append(FadeOut(sg, run_time=self.run_time))

        # Unmatched target glyphs: FadeIn from their position
        for tgt_i in sorted(unmatched_tgt):
            if tgt_i < len(tgt_glyphs):
                tg = tgt_glyphs[tgt_i]
                leaves = _iter_vmobjects(tg) if isinstance(tg, VGroup) else [tg]
                self._new_mobs.extend(leaves)
                # Let FadeIn.begin() zero and restore opacity correctly
                self._inner.append(FadeIn(tg, run_time=self.run_time))

        for anim in self._inner:
            anim.begin()

    def interpolate(self, alpha: float) -> None:
        for anim in self._inner:
            anim_alpha = min(alpha * self.run_time / anim.run_time, 1.0)
            anim.interpolate(anim_alpha)

    def finish(self) -> None:
        for anim in self._inner:
            anim.finish()
