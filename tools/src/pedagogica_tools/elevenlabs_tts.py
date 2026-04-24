"""ElevenLabs Speech-Synthesis-with-Timestamps wrapper.

POST to /v1/text-to-speech/{voice_id}/with-timestamps, decode the
base64 audio, convert char-level alignment to WordTiming list,
write clip.mp3 + AudioClip JSON.
"""

from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import httpx

from pedagogica_schemas.audio import AudioClip, WordTiming

_BASE_URL = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_CHAR_QUOTA = 10_000


@dataclass
class TtsOptions:
    model_id: str = DEFAULT_MODEL_ID
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True
    # Speech rate multiplier. 1.0 = default ElevenLabs pace. Lower = slower.
    # Explainer-video default is 0.75: noticeably calmer pace suited to math/physics
    # narration where the viewer needs time to absorb each beat.
    # Acceptable range is roughly 0.7-1.2 per ElevenLabs.
    speed: float = 0.75
    char_quota: int = DEFAULT_CHAR_QUOTA
    timeout_seconds: float = 90.0
    extra_voice_settings: dict = field(default_factory=dict)


def _chars_to_word_timings(
    characters: list[str],
    char_starts: list[float],
    char_ends: list[float],
) -> list[WordTiming]:
    """Group ElevenLabs char-level alignment into word-level WordTiming list.

    Builds text from the returned characters (safer than using raw input text,
    since ElevenLabs may normalise the input before alignment). Word boundaries
    = runs of non-whitespace characters.
    """
    joined = "".join(characters)
    timings: list[WordTiming] = []

    for match in re.finditer(r"\S+", joined):
        start_ci = match.start()
        end_ci = match.end() - 1  # inclusive

        # Guard against alignment arrays shorter than text (edge case).
        if start_ci >= len(char_starts):
            continue
        safe_end = min(end_ci, len(char_ends) - 1)

        timings.append(
            WordTiming(
                word=match.group(),
                start_seconds=char_starts[start_ci],
                end_seconds=char_ends[safe_end],
                char_start=start_ci,
                char_end=end_ci + 1,
            )
        )

    return timings


def synthesize(
    *,
    text: str,
    voice_id: str,
    output_mp3_path: Path | str,
    scene_id: str,
    options: TtsOptions | None = None,
    result_json_path: Path | str | None = None,
) -> AudioClip:
    """Call ElevenLabs TTS with timestamps; write mp3 and return AudioClip."""
    opts = options or TtsOptions()
    output_mp3_path = Path(output_mp3_path)

    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError("ELEVENLABS_API_KEY is not set")

    char_count = len(text)
    if char_count > opts.char_quota:
        raise ValueError(
            f"text is {char_count} chars, exceeds quota {opts.char_quota}"
        )

    voice_settings: dict = {
        "stability": opts.stability,
        "similarity_boost": opts.similarity_boost,
        "style": opts.style,
        "use_speaker_boost": opts.use_speaker_boost,
        "speed": opts.speed,
        **opts.extra_voice_settings,
    }

    url = f"{_BASE_URL}/text-to-speech/{voice_id}/with-timestamps"
    payload = {
        "text": text,
        "model_id": opts.model_id,
        "voice_settings": voice_settings,
    }

    with httpx.Client(timeout=opts.timeout_seconds) as client:
        resp = client.post(
            url,
            json=payload,
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
            },
        )

    resp.raise_for_status()
    data = resp.json()

    # Write audio bytes
    audio_bytes = base64.b64decode(data["audio_base64"])
    output_mp3_path.parent.mkdir(parents=True, exist_ok=True)
    output_mp3_path.write_bytes(audio_bytes)

    # Parse alignment (prefer normalized_alignment when present)
    alignment = data.get("normalized_alignment") or data.get("alignment") or {}
    characters: list[str] = alignment.get("characters", [])
    char_starts: list[float] = alignment.get("character_start_times_seconds", [])
    char_ends: list[float] = alignment.get("character_end_times_seconds", [])

    word_timings = _chars_to_word_timings(characters, char_starts, char_ends)
    total_duration = char_ends[-1] if char_ends else 0.0

    clip = AudioClip(
        trace_id=uuid4(),
        span_id=uuid4(),
        producer="elevenlabs-tts",
        scene_id=scene_id,
        audio_path=str(output_mp3_path.resolve()),
        total_duration_seconds=total_duration,
        word_timings=word_timings,
        voice_id=voice_id,
        model_id=opts.model_id,
        char_count=char_count,
    )

    if result_json_path is not None:
        p = Path(result_json_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(clip.model_dump_json(indent=2))

    return clip
