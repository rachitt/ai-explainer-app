"""Tests for pedagogica-tools elevenlabs-tts.

Unit tests mock the HTTP call so no real API key is needed.
The live integration test is skipped unless ELEVENLABS_API_KEY is set.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pedagogica_schemas.audio import AudioClip, WordTiming
from pedagogica_tools.elevenlabs_tts import (
    TtsOptions,
    _chars_to_word_timings,
    synthesize,
)


# ── unit: char-to-word grouping ───────────────────────────────────────────────

def test_chars_to_word_timings_basic() -> None:
    chars  = list("hello world")
    starts = [i * 0.1 for i in range(len(chars))]
    ends   = [(i + 1) * 0.1 for i in range(len(chars))]
    timings = _chars_to_word_timings(chars, starts, ends)
    assert len(timings) == 2
    assert timings[0].word == "hello"
    assert timings[1].word == "world"
    assert timings[0].start_seconds == pytest.approx(0.0)
    assert timings[0].end_seconds   == pytest.approx(0.5)
    assert timings[1].start_seconds == pytest.approx(0.6)
    assert timings[1].end_seconds   == pytest.approx(1.1)


def test_chars_to_word_timings_empty() -> None:
    assert _chars_to_word_timings([], [], []) == []


def test_chars_to_word_timings_short_alignment() -> None:
    # Alignment array shorter than text — should skip, not raise.
    chars  = list("hi there")
    starts = [0.0, 0.1]   # only first 2 chars have timings
    ends   = [0.1, 0.2]
    timings = _chars_to_word_timings(chars, starts, ends)
    assert len(timings) == 1
    assert timings[0].word == "hi"


# ── unit: quota guard ─────────────────────────────────────────────────────────

def test_synthesize_quota_exceeded(tmp_path: Path) -> None:
    os.environ["ELEVENLABS_API_KEY"] = "test-key"
    with pytest.raises(ValueError, match="exceeds quota"):
        synthesize(
            text="a" * 100,
            voice_id="some-voice",
            output_mp3_path=tmp_path / "out.mp3",
            scene_id="scene_01",
            options=TtsOptions(char_quota=10),
        )


def test_synthesize_missing_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="ELEVENLABS_API_KEY"):
        synthesize(
            text="hello",
            voice_id="some-voice",
            output_mp3_path=tmp_path / "out.mp3",
            scene_id="scene_01",
        )


# ── unit: mock HTTP round-trip ────────────────────────────────────────────────

def _fake_response(text: str) -> MagicMock:
    chars  = list(text)
    starts = [round(i * 0.08, 3) for i in range(len(chars))]
    ends   = [round((i + 1) * 0.08, 3) for i in range(len(chars))]
    body = {
        "audio_base64": base64.b64encode(b"FAKE_AUDIO").decode(),
        "alignment": {
            "characters": chars,
            "character_start_times_seconds": starts,
            "character_end_times_seconds": ends,
        },
    }
    mock = MagicMock()
    mock.json.return_value = body
    mock.raise_for_status.return_value = None
    return mock


@patch("pedagogica_tools.elevenlabs_tts.httpx.Client")
def test_synthesize_writes_mp3_and_json(mock_client_cls: MagicMock, tmp_path: Path) -> None:
    os.environ["ELEVENLABS_API_KEY"] = "test-key"

    text = "chain rule"
    mock_post = MagicMock(return_value=_fake_response(text))
    mock_client_cls.return_value.__enter__.return_value.post = mock_post

    out_mp3  = tmp_path / "tts.mp3"
    out_json = tmp_path / "timing.json"

    clip = synthesize(
        text=text,
        voice_id="voice-abc",
        output_mp3_path=out_mp3,
        scene_id="scene_01",
        result_json_path=out_json,
    )

    assert out_mp3.read_bytes() == b"FAKE_AUDIO"
    assert out_json.exists()
    assert clip.scene_id == "scene_01"
    assert clip.char_count == len(text)
    assert len(clip.word_timings) == 2
    assert clip.word_timings[0].word == "chain"
    assert clip.word_timings[1].word == "rule"

    # JSON round-trips to valid AudioClip
    loaded = AudioClip.model_validate_json(out_json.read_text())
    assert loaded.scene_id == clip.scene_id


# ── integration: real API (skipped without key) ───────────────────────────────

HAVE_KEY = bool(os.environ.get("ELEVENLABS_API_KEY", "").strip())
skip_no_key = pytest.mark.skipif(not HAVE_KEY, reason="ELEVENLABS_API_KEY not set")

RACHEL_VOICE = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs "Rachel" — free tier


@skip_no_key
def test_live_synthesize_short_phrase(tmp_path: Path) -> None:
    clip = synthesize(
        text="Ohm's Law states V equals I times R.",
        voice_id=RACHEL_VOICE,
        output_mp3_path=tmp_path / "live.mp3",
        scene_id="live_test",
        options=TtsOptions(char_quota=200),
    )
    assert (tmp_path / "live.mp3").stat().st_size > 1_000
    assert clip.total_duration_seconds > 0
    assert len(clip.word_timings) >= 5
    for wt in clip.word_timings:
        assert wt.end_seconds >= wt.start_seconds
