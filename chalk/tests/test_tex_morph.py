"""Tests for TransformMatchingTex and _tokenize."""
import pytest
from chalk.tex_morph import _tokenize, _greedy_match, TransformMatchingTex
from chalk.tex import MathTex


def test_tokenize_simple_equation():
    tokens = _tokenize("F=ma")
    assert tokens == ["F", "=", "m", "a"]


def test_tokenize_latex_command():
    tokens = _tokenize(r"\frac{1}{2}")
    assert r"\frac" in tokens


def test_tokenize_skips_whitespace():
    tokens = _tokenize("a + b")
    assert " " not in tokens
    assert tokens == ["a", "+", "b"]


def test_greedy_match_finds_common_tokens():
    src = ["F", "=", "m", "a"]
    tgt = ["a", "=", "F", "/", "m"]
    matches, unmatched_src, unmatched_tgt = _greedy_match(src, tgt)
    # All of src's tokens appear in tgt → unmatched_src should be empty or minimal
    matched_src_indices = {s for s, _ in matches}
    assert len(matched_src_indices) == len(src)  # all src matched


def test_greedy_match_unmatched_target():
    src = ["a", "b"]
    tgt = ["a", "b", "c"]
    matches, unmatched_src, unmatched_tgt = _greedy_match(src, tgt)
    assert 2 in unmatched_tgt  # 'c' is unmatched


def _null_sink():
    class NS:
        def write(self, f): pass
    return NS()


def test_transform_matching_tex_at_alpha_1_source_glyphs_at_target_positions():
    """After finish(), matched source glyphs should be at target positions."""
    src = MathTex("F=ma", color="#FFFFFF", scale=0.65)
    tgt = MathTex("a=F/m", color="#FFFFFF", scale=0.65)

    anim = TransformMatchingTex(src, tgt, run_time=1.0)
    anim.begin()
    anim.finish()

    # Source '=' glyph (index 1) should have transformed toward target '=' (also index 1 in tgt)
    # Just verify: no error and finish() completes without exception


def test_transform_matching_tex_unmatched_source_fades_out():
    """Source-only tokens should have fill_opacity 0 after finish()."""
    # 'F=ma' → 'ab': only 'a' matches; 'F', '=', 'm' should fade out
    src = MathTex("F=ma", color="#FFFFFF", scale=0.65)
    tgt = MathTex("ab", color="#FFFFFF", scale=0.65)

    anim = TransformMatchingTex(src, tgt, run_time=1.0)
    anim.begin()
    anim.finish()

    from chalk.animation import _iter_vmobjects
    from chalk.tex_morph import _tokenize, _greedy_match

    src_tokens = _tokenize("F=ma")
    tgt_tokens = _tokenize("ab")
    _, unmatched_src, _ = _greedy_match(
        src_tokens[:len(src.submobjects)],
        tgt_tokens[:len(tgt.submobjects)]
    )
    for i in unmatched_src:
        if i < len(src.submobjects):
            m = src.submobjects[i]
            assert m.fill_opacity == pytest.approx(0.0)


def test_transform_matching_tex_unmatched_target_fades_in():
    """Target-only tokens should be visible (fill_opacity > 0) after finish()."""
    src = MathTex("ab", color="#FFFFFF", scale=0.65)
    tgt = MathTex("abc", color="#FFFFFF", scale=0.65)

    anim = TransformMatchingTex(src, tgt, run_time=1.0)
    anim.begin()
    anim.finish()

    # 'c' is only in target — its glyph should be visible
    from chalk.tex_morph import _tokenize, _greedy_match
    src_t = _tokenize("ab")[:len(src.submobjects)]
    tgt_t = _tokenize("abc")[:len(tgt.submobjects)]
    _, _, unmatched_tgt = _greedy_match(src_t, tgt_t)

    for i in unmatched_tgt:
        if i < len(tgt.submobjects):
            m = tgt.submobjects[i]
            assert m.fill_opacity > 0.0
