---
name: audio-visual-sync
version: 0.1.0
category: knowledge
description: >
  How to map Manim animation timings to ElevenLabs word timings to produce a
  SyncPlan. Covers anchor-word selection, drift measurement, and the
  animation-offset model.
owner: rachit
last_reviewed: 2026-04-21
---

# Audio-Visual Sync

## The sync problem

Manim renders video at a fixed frame rate independent of narration speed. ElevenLabs
produces audio at its own pace. The `sync` agent's job is to produce a `SyncPlan`
that tells the mux stage when (in audio-time seconds) each Manim animation should
begin, so the visuals match what the narrator is saying.

## Core model

Every `SceneAnimation` in `spec.json` has an `id` and a `run_time`. Every narration
sentence (from `script.json`) has `markers` — named cue points tied to specific words.

The sync algorithm:

1. For each marker in the script, find the word in `timing.json` (the `AudioClip`)
   whose text matches the marker's `anchor_word`.
2. The animation referenced by the marker starts at `word.start_seconds - lead_seconds`
   (default `lead_seconds = 0.1` — start slightly before the word is spoken).
3. `run_time` comes from the spec; `wait_after_seconds` fills the gap to the next marker.

## SyncPlan schema

```json
{
  "scene_id": "scene_02",
  "timings": [
    {
      "animation_id": "anim_01",
      "start_seconds": 0.85,
      "run_time_seconds": 1.0,
      "wait_after_seconds": 0.3,
      "anchored_word_indices": [4, 5]
    }
  ],
  "total_scene_duration": 28.4,
  "audio_offset_seconds": 0.0,
  "drift_seconds": 0.0
}
```

`drift_seconds` is set to 0.0 at plan time; `measure-drift` fills it after render.

## Anchor word selection rules

- Pick the **content word that visually fires with**: the noun, verb, or symbol the
  animation is introducing. Not prepositions or articles.
- Good: `"the derivative"` → anchor on `"derivative"`.
- Bad: `"when we look at"` → anchor on `"look"` or `"at"` would be too vague.
- If a scene has no markers (all visual, no narration), distribute animations evenly
  across the audio duration.

## Lead time constants

| Animation type | lead_seconds |
|---|---|
| `Write` / `FadeIn` of a formula | 0.15 |
| `GrowArrow`, `Create` of a shape | 0.10 |
| `Indicate` / `Circumscribe` (highlight) | 0.05 |
| `Transform` / `ReplacementTransform` | 0.20 |

Lead time prevents the visual from lagging behind the spoken word.

## Drift tolerance

Target: ≤ 0.15s drift on ≥ 80% of anchored animations (Phase 1 success criterion).

Drift > 0.3s on any anchor = repair trigger. The repair strategy (from `retry-strategy`)
is to adjust `lead_seconds` for that animation type globally, then re-sync.

## Animation time budget

If the total `sum(run_time + wait_after)` across all animations exceeds
`audio_clip.total_duration_seconds`, the video will be longer than the audio.
In that case, proportionally shrink all `wait_after_seconds` values (never `run_time`).

## No-narration scenes

Some scenes are purely visual (title cards, transition beats). For these:
- Set `audio_offset_seconds` to the cumulative audio position from prior scenes.
- Distribute animations with `run_time` as specified and uniform `wait_after` gaps.
- `drift_seconds` = 0.0 (no anchor to measure against).
