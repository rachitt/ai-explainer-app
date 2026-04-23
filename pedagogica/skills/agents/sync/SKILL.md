---
name: sync
version: 0.2.0
category: orchestration
triggers:
  - stage:sync
requires: []
token_estimate: 1400
tested_against_model: claude-sonnet-4-6
owner: rachit
last_reviewed: 2026-04-22
description: >
  Reads a scene's Script markers + AudioClip word timings and emits a SyncPlan
  mapping each marker's element ref to an absolute start time in the narration.
  Rule-based, near-deterministic — Sonnet, not Opus. Phase 1 operates without a
  SceneSpec; run_times come from a marker-type heuristic, not from spec animations.
---

# Sync agent

## Purpose

Read `scenes/<scene_id>/script.json` and `scenes/<scene_id>/audio/clip.json`, and emit `scenes/<scene_id>/sync.json` (`SyncPlan`). The sync plan is how downstream (ffmpeg-mux, chalk-code re-emit, subtitle-gen, future editor) knows *when* each visual element should appear inside the narration.

Deterministic mapping. No creative reasoning.

## Phase 1 simplifications

- **No `spec.json`.** The trimmed roster folds visual-planner into chalk-code, so scene specs are not a separate artifact. `run_time_seconds` comes from a per-`marker_type` heuristic, not from `spec.animations[*].run_time`.
- **No `tts.json`.** Audio clip lives at `audio/clip.json` (filename produced by `pedagogica-tools elevenlabs-tts`).
- **Per-scene only.** Inter-scene offsets (multi-scene timeline) are handled by `ffmpeg-mux` via `concat`, not here. `audio_offset_seconds = 0.0`.

## Inputs

- `artifacts/<job_id>/scenes/<scene_id>/script.json` — `Script`. Each entry in `markers` has:
  - `word_index: int` — 0-based index into `script.words`.
  - `marker_type: "show" | "highlight" | "pause" | "transition"`.
  - `ref: str` — scene-DSL element id (e.g. `"eq.composition"`, `"graph.parabola"`, `"pause"` for `pause` markers).
- `artifacts/<job_id>/scenes/<scene_id>/audio/clip.json` — `AudioClip`. Contains `word_timings` (list of `WordTiming` with `word`, `start_seconds`, `end_seconds`) and `total_duration_seconds`.
- `artifacts/<job_id>/job_state.json` — for `trace_id`.

The `script.words` and `clip.word_timings` lists are expected to line up 1:1 by index. Tokenization matches: ElevenLabs returns one `WordTiming` per whitespace-separated script token. Mismatches are an upstream bug — surface loudly, don't paper over.

## Output

Write `artifacts/<job_id>/scenes/<scene_id>/sync.json` (`SyncPlan`):

```json
{
  "trace_id": "<uuid copied from job_state>",
  "span_id": "<fresh uuid>",
  "parent_span_id": "<clip.json span_id>",
  "timestamp": "<utc ISO8601>",
  "producer": "sync",
  "schema_version": "0.1.0",
  "scene_id": "<scene_id>",
  "timings": [
    {
      "animation_id": "eq.composition",
      "start_seconds": 0.71,
      "run_time_seconds": 0.8,
      "wait_after_seconds": 0.4,
      "anchored_word_indices": [7]
    }
  ],
  "total_scene_duration": 17.508,
  "audio_offset_seconds": 0.0,
  "drift_seconds": 0.0
}
```

- `timings[*].animation_id` carries the marker's `ref` verbatim. (The SyncPlan field name predates the roster trim; `ref` is the same thing in the current pipeline — the chalk-code element id the marker anchors to.)
- `anchored_word_indices` is a single-element list containing the marker's `word_index`. Keep it a list for forward-compat with multi-word anchors.
- `drift_seconds = 0.0` always — filled post-render by `measure-drift`.
- `audio_offset_seconds = 0.0` always in Phase 1.
- `parent_span_id` = `clip.json` `span_id`.

## Algorithm

1. Validate inputs:
   - `len(script.words) == len(clip.word_timings)`. If not, halt — this is a tokenization drift bug upstream.
   - Every `marker.word_index` is in `[0, len(script.words))`.

2. For each `marker` in `script.markers`, in order of `word_index`:
   - `start_seconds = clip.word_timings[marker.word_index].start_seconds - lead_time(marker.marker_type)`. Clamp to `≥ 0`.
   - `run_time_seconds = RUN_TIME_BY_TYPE[marker.marker_type]` (see below).
   - Emit an `AnimationTiming` with `animation_id = marker.ref`, `anchored_word_indices = [marker.word_index]`. Leave `wait_after_seconds` at `0` for now; pass 2 fills it in.

3. Pass 2 — compute `wait_after_seconds`:
   - For each timing `T[i]` except the last: `T[i].wait_after = max(0, T[i+1].start - (T[i].start + T[i].run_time))`.
   - For the last timing: `T[-1].wait_after = max(0, clip.total_duration_seconds - (T[-1].start + T[-1].run_time))`.

4. Set `total_scene_duration = clip.total_duration_seconds` (video length = audio length in Phase 1; visuals are clamped to audio by `ffmpeg-mux`).

5. If `sum(run_time) > clip.total_duration_seconds` — a scene packed with back-to-back markers with no breathing room: halt and surface. Don't silently shrink `run_time`s. This indicates the script crammed too many markers for the duration; fix upstream.

## Heuristics

```
LEAD_TIME_BY_TYPE = {
  "show":       0.15,   # small visual lead so element appears ~150ms before word lands
  "highlight":  0.10,
  "pause":      0.00,   # pauses anchor on the word boundary exactly
  "transition": 0.25,   # transitions start earlier so the destination is on-screen when word hits
}

RUN_TIME_BY_TYPE = {
  "show":       0.8,
  "highlight":  0.5,
  "pause":      0.4,
  "transition": 0.6,
}
```

These are Phase 1 defaults chosen from the kvl_001 reference. If a particular scene needs bespoke timing, the chalk-code agent can override on re-emit — sync is the baseline, not the ceiling.

## Edge cases

- **Zero markers.** Emit `timings = []`, `total_scene_duration = clip.total_duration_seconds`. Downstream (ffmpeg-mux) still muxes the scene; just no anchored visuals.
- **Two markers on the same `word_index`.** Allowed. They share a start time; second one runs after first's `run_time` via pass 2 `wait_after`.
- **Marker on the very first or very last word.** First-word: `start_seconds` may clamp to 0 after subtracting lead. Last-word: pass 2 may set `wait_after = 0`.
- **Unicode / punctuation drift between `script.words` and `clip.word_timings[].word`.** Do not cross-check text — the index is the SSOT. If ElevenLabs returned a different word count than the script tokenization, halt (step 1 validation).

## Hard rules

- Do **not** parse `spec.json` — it does not exist in Phase 1.
- Do **not** modify `script.json` or `clip.json`. Sync is read-only on its inputs.
- Do **not** set `drift_seconds` to anything other than `0.0` — that's `measure-drift`'s field.
- Do **not** write any other file under the scene dir. One input-triple → one `sync.json`.

## Validation

```
uv run pedagogica-tools validate SyncPlan artifacts/<job_id>/scenes/<scene_id>/sync.json
```

Non-zero exit → the orchestrator retries once with the validator's stderr, then hard-fails.
