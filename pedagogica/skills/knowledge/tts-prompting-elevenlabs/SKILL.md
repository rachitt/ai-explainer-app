---
name: tts-prompting-elevenlabs
version: 0.1.0
category: knowledge
description: >
  Voice selection, model IDs, SSML-lite prompting, and voice settings for
  ElevenLabs Speech-Synthesis-with-Timestamps. Covers rate/pause control,
  pronunciation fixes, and the char-quota cost model.
owner: rachit
last_reviewed: 2026-04-21
---

# ElevenLabs TTS Prompting

## API endpoint

`POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps`

Response includes `audio_base64` + `alignment.characters` / `character_start_times_seconds` /
`character_end_times_seconds`. Use `normalized_alignment` when present — it's cleaner.

## Model IDs (Phase 1)

| Model | Use when |
|---|---|
| `eleven_multilingual_v2` | Default. Best quality, good timing accuracy. |
| `eleven_turbo_v2_5` | Fast iteration / cheap test runs. Lower fidelity. |

Always pass `model_id` explicitly — do not rely on ElevenLabs defaults changing.

## Voice selection

Phase 1: English only. Recommended voices for educational content:

| Voice ID | Name | Character |
|---|---|---|
| `21m00Tcm4TlvDq8ikWAM` | Rachel | Calm, clear, neutral American |
| `AZnzlk1XvdvUeBnXmlld` | Domi | Confident, slightly warmer |
| `ErXwobaYiN019PkySvjV` | Antoni | Male, measured, good for math |

Default to **Rachel** (`21m00Tcm4TlvDq8ikWAM`) for all Phase 1 calculus videos.

## Voice settings

```json
{
  "stability": 0.5,
  "similarity_boost": 0.75,
  "style": 0.0,
  "use_speaker_boost": true
}
```

- `stability 0.5` — balanced consistency vs. naturalness.
- `style 0.0` — keep it flat; style > 0 adds emotional variance that sounds odd for math.
- Never set `stability > 0.85` (robotic) or `stability < 0.3` (inconsistent across sentences).

## Text preparation rules

1. **No LaTeX or MathTex strings in the narration.** Write out math in words.
   - Bad: `"The derivative is $\frac{dy}{dx}$"`
   - Good: `"The derivative is d-y over d-x"`

2. **Spell out symbols.** `Ω` → `ohms`, `∫` → `integral`, `×` → `times`.

3. **Use commas for natural pauses.** ElevenLabs respects punctuation pacing.
   - `"First, isolate the inner function. Then, differentiate the outer."` — correct.

4. **Abbreviations.** Write `f prime of x` not `f'(x)`. Write `x squared` not `x^2`.

5. **Numbers.** Write `12 volts` not `12V`; `4 ohms` not `4Ω`.

6. **Keep sentences short.** 15–25 words per sentence. Longer sentences drift in timing.

## Pause injection

ElevenLabs does not support SSML `<break>` in the standard API. Use punctuation instead:

| Desired pause | Technique |
|---|---|
| Short (0.2s) | Comma |
| Medium (0.5s) | Period + new sentence |
| Long (1s+) | Split into separate TTS calls |

Do **not** inject silence via empty strings — they produce no alignment entries and break
the word→animation sync mapping.

## Cost model and quota

`eleven_multilingual_v2` costs ~$0.30 per 1 000 chars (as of 2026-04-21).

Default per-scene quota: **10 000 chars ≈ $3.00** (enforced by `TtsOptions.char_quota`).

Typical narration length:
- 30-second scene: ~400–600 chars
- 60-second scene: ~800–1 200 chars

A 3-minute video (6 scenes × 30s) ≈ 3 000–4 500 chars total ≈ $0.90–$1.35.
The 10 000-char quota is a hard ceiling, not a target.

## Timing accuracy expectations

- Word-level accuracy: ±50ms for most words in `eleven_multilingual_v2`.
- Boundary words (first/last of sentence): ±80ms.
- Gaps at utterance boundaries (between sentences): can be 100–300ms; watch for these
  when anchoring animations to word indices.
