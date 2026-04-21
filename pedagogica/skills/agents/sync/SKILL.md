---
name: sync
version: 0.1.0
category: orchestration
triggers:
  - stage:sync
requires:
  - audio-visual-sync@^0.1.0
  - tts-prompting-elevenlabs@^0.1.0
token_estimate: 1800
tested_against_model: claude-sonnet-4-6
owner: rachit
last_reviewed: 2026-04-21
description: >
  Produces a SyncPlan by mapping SceneAnimation IDs to ElevenLabs word timings.
  Reads script markers + AudioClip word timings; emits sync.json. Near-deterministic
  — uses Sonnet, not Opus.
---

# Sync agent

## Purpose

Read the scene's `script.json`, `spec.json`, and `tts.json` (AudioClip), and emit
`sync.json` (SyncPlan). This is the glue between the visual tier and the audio tier.
No creative reasoning required — the mapping is rule-based (see `audio-visual-sync`).

## Inputs

- `artifacts/<job_id>/scenes/<scene_id>/script.json` — `Script`. Use `markers` for
  named anchor points. Each marker has `animation_id` and `anchor_word`.
- `artifacts/<job_id>/scenes/<scene_id>/spec.json` — `SceneSpec`. Use `animations[].run_time`
  for each animation's duration. Do not invent run_times.
- `artifacts/<job_id>/scenes/<scene_id>/tts.json` — `AudioClip`. Contains `word_timings`
  (list of `WordTiming`) and `total_duration_seconds`.

## Output

Write `artifacts/<job_id>/scenes/<scene_id>/sync.json` — a `SyncPlan`:

```json
{
  "trace_id": "<uuid>",
  "span_id": "<uuid>",
  "parent_span_id": "<tts_span_id>",
  "timestamp": "<utc>",
  "producer": "sync",
  "schema_version": "0.1.0",
  "scene_id": "<scene_id>",
  "timings": [
    {
      "animation_id": "anim_01",
      "start_seconds": 0.85,
      "run_time_seconds": 1.0,
      "wait_after_seconds": 0.4,
      "anchored_word_indices": [4, 5]
    }
  ],
  "total_scene_duration": 28.4,
  "audio_offset_seconds": 0.0,
  "drift_seconds": 0.0
}
```

- Set `drift_seconds = 0.0` always — it is filled post-render by `measure-drift`.
- Set `audio_offset_seconds = 0.0` for now (multi-scene offset is the editor's job).
- `parent_span_id` = `tts.json`'s `span_id`.

## Algorithm

1. Build a word index from `tts.json`: `{word_text: [WordTiming, ...]}`.
   - Multiple occurrences of the same word → keep all; disambiguate by position.

2. For each `marker` in `script.markers` (in order):
   a. Find the target `WordTiming` matching `marker.anchor_word` at approximately
      the expected position in the narration.
   b. Compute `start_seconds = word.start_seconds - lead_time(animation_type)`.
      Lead times from `audio-visual-sync`.
   c. Look up `run_time_seconds` from `spec.animations` for `marker.animation_id`.
   d. `wait_after_seconds` = time until the next anchor's `start_seconds` minus
      `start_seconds + run_time_seconds`. Clamp to ≥ 0.

3. For animations in `spec.animations` with no corresponding marker:
   - Place them sequentially after the last anchored animation, with `wait_after = 0.3`.

4. Compute `total_scene_duration`:
   - `max(tts.total_duration_seconds, sum(run_time + wait_after for all animations))`

5. If `sum(run_time + wait_after) > tts.total_duration_seconds`:
   - Scale down all `wait_after_seconds` proportionally (never change `run_time`).
   - Log a warning in the output JSON comment field if schema supports it.

## Word matching

- Case-insensitive match.
- Strip trailing punctuation before comparing (`"First," → "First"`).
- If `anchor_word` does not match any word in the timing list, use the closest
  word by edit distance ≤ 2. If still no match, use `tts.total_duration_seconds * position_fraction`
  as a fallback and flag the animation with `anchored_word_indices: []`.

## Common mistakes

- **Using spec run_times as timing anchors.** Don't. run_time is for the animation
  duration only. The start time comes from the word timing.
- **Setting drift_seconds to anything other than 0.0.** Leave it at 0. It's
  a measurement field.
- **Missing animations.** Every `animation_id` in `spec.animations` must appear
  exactly once in `timings`. If a spec animation has no marker, place it after the
  last anchored one.
