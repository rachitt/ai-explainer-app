from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pedagogica_tools.cli import app
from pedagogica_tools.tts_preproc import PronunciationRule, apply_rules
from typer.testing import CliRunner


runner = CliRunner()


def test_apply_rules_basic() -> None:
    text = "Using Bernoulli's equation, rho v squared is important."

    result, fired = apply_rules(text)

    assert len(fired) >= 2
    assert "Bernooli's" in result
    assert "roe v squared" in result


def test_apply_rules_case_insensitive() -> None:
    result, fired = apply_rules("bernoulli and BERNOULLI")

    assert result == "Bernooli and Bernooli"
    assert [rule.pattern for rule in fired] == [r"\bBernoulli\b"]


def test_apply_rules_word_boundary() -> None:
    result, fired = apply_rules("A rhombus is not rho.")

    assert "rhombus" in result
    assert "roe" in result
    assert [rule.pattern for rule in fired] == [r"\brho\b"]


def test_apply_rules_preserves_word_count() -> None:
    original = "Bernoulli used theta while Euler studied incompressible flow."

    result, _ = apply_rules(original)

    assert len(result.split()) == len(original.split())


def test_multi_token_replacement_raises() -> None:
    rules = (PronunciationRule(r"\bone\b", "two words", "invalid replacement"),)

    with pytest.raises(ValueError, match="single token"):
        apply_rules("one", rules)


def test_no_rules_matched_returns_original() -> None:
    text = "Plain English with no dictionary hits."

    result, fired = apply_rules(text)

    assert result == text
    assert fired == []


@patch("pedagogica_tools.elevenlabs_tts.synthesize")
def test_cli_pronounce_flag(mock_synthesize: MagicMock, tmp_path: Path) -> None:
    text_path = tmp_path / "narration.txt"
    text_path.write_text("Bernoulli says rho matters.", encoding="utf-8")
    mock_clip = MagicMock()
    mock_clip.model_dump_json.return_value = '{"ok": true}'
    mock_synthesize.return_value = mock_clip

    result = runner.invoke(
        app,
        [
            "elevenlabs-tts",
            str(text_path),
            "voice-abc",
            str(tmp_path / "tts.mp3"),
            "--scene-id",
            "scene_01",
        ],
    )

    assert result.exit_code == 0, result.stderr
    called_text = mock_synthesize.call_args.kwargs["text"]
    assert "Bernooli" in called_text
    assert "roe" in called_text
    assert (tmp_path / "narration.txt.rewritten.txt").read_text(
        encoding="utf-8"
    ) == called_text
    assert "pronunciation rules fired:" in result.stderr
