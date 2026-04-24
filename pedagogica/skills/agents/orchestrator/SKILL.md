---
name: orchestrator
version: 0.0.1
category: orchestration
triggers:
  - command:/pedagogica
requires: []
token_estimate: 1800
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Drives the Pedagogica agent DAG for a single job. Phase 1 scope ships the
  planning tier (intake → curriculum → storyboard); later tiers wire in from
  subsequent worktrees. Reads/writes JSON artifacts under artifacts/<job_id>/
  and delegates schema validation to `uv run pedagogica-tools validate`.
---

# Orchestrator (Phase 1)

## Purpose

Single point of control for a `/pedagogica` job. Walks stages in DAG order, persists `job_state.json` on every transition, validates every emitted artifact, appends trace events, and stops cleanly on failure so `/pedagogica resume` works.

## Input contract

You are invoked with one of two modes:

- `start` — a fresh `job_state.json` already exists at `artifacts/<job_id>/job_state.json`; all stages are `pending`; `current_stage` = `intake`.
- `resume` — an existing `job_state.json`; pick the first non-`complete` stage.

Never allocate a `job_id` yourself — the `/pedagogica` command does that before invoking you.

## Stage table (Phase 1)

| Stage | Agent skill / tool | Output artifact | Output schema | Fan-out |
|---|---|---|---|---|
| intake | `agents/intake/SKILL.md` | `01_intake.json` | `IntakeResult` | once per job |
| curriculum | `agents/curriculum/SKILL.md` | `02_curriculum.json` | `CurriculumPlan` | once per job |
| storyboard | `agents/storyboard/SKILL.md` | `03_storyboard.json` | `Storyboard` | once per job |
| script | `agents/script/SKILL.md` | `scenes/<scene_id>/script.json` | `Script` | once per scene in `storyboard.scenes` |
| chalk-code | `agents/chalk-code/SKILL.md` (+ `agents/chalk-repair/SKILL.md` on failure) | `scenes/<scene_id>/code.py` + `code.json` + `<scene_id>.mp4` | `ChalkCode` (for `code.json`); `CompileResult` (for each `compile_attempt_<N>.json`) | once per scene; includes render + up to 3 repair attempts |
| tts | `uv run pedagogica-tools elevenlabs-tts` (non-LLM) | `scenes/<scene_id>/audio/clip.mp3` + `scenes/<scene_id>/audio/clip.json` | `AudioClip` | once per scene |
| sync | `agents/sync/SKILL.md` | `scenes/<scene_id>/sync.json` | `SyncPlan` | once per scene |
| editor | `uv run pedagogica-tools ffmpeg-mux` (non-LLM) | `scenes/<scene_id>/synced.mp4` + `<job_dir>/final.mp4` | — (tool emits mp4 only; no JSON schema) | whole job |
| subtitle | `uv run pedagogica-tools subtitle-gen` (non-LLM) | `scenes/<scene_id>/synced.vtt` + `.srt` + `<job_dir>/captions.vtt` + `captions.srt` | — (tool emits sidecars; no JSON schema) | whole job |

All nine stages ship in this tier. After `subtitle` completes, the orchestrator flips `terminal = true`. Critics and cost-cap enforcement are later tiers.

## Per-stage protocol

For each stage `S` with `status != complete`:

1. **Pre-flight** — re-validate the upstream artifact it depends on. Example: before `curriculum`, run
   `uv run pedagogica-tools validate IntakeResult artifacts/<job_id>/01_intake.json`. Non-zero exit = abort.
2. **Mark in-progress** — rewrite `job_state.json` with `stages[S].status = "in_progress"`, `started_at = <ISO8601-UTC>`, `current_stage = S`. Validate:
   `uv run pedagogica-tools validate JobState artifacts/<job_id>/job_state.json`.
3. **Invoke the agent** — load the agent's `SKILL.md` and follow its instructions. The agent writes the output artifact and only the output artifact.
4. **Validate the output** — `uv run pedagogica-tools validate <Schema> artifacts/<job_id>/<NN_stage>.json`.
   - Exit 0 → continue.
   - Exit 1 (validation) → re-prompt the agent once with the validator's stderr; second failure is a hard fail.
   - Exit 2 (usage/IO) → hard fail.
   - After storyboard JSON is written and schema-validated, run:
     ```
     uv run pedagogica-tools check-storyboard artifacts/<job_id>/03_storyboard.json
     ```
     - Exit 1 on `lo_cap` → re-prompt the storyboard agent once with the failing report. Second failure halts the stage.
     - Exit 2 (usage/IO) → hard fail.
5. **Mark complete** — `stages[S].status = "complete"`, `completed_at`, `artifact_path = "<NN_stage>.json"`, advance `current_stage` to the next non-complete stage (or `null` at end of tier). Rewrite and re-validate `job_state.json`.
6. **Trace** — `uv run pedagogica-tools trace <job_id> '<event-json>'` with a `stage_exit` event. (Trace CLI is stubbed in this worktree; the call is still made so the shape is fixed.)

### Per-scene stages (fan-out)

`script` and `chalk-code` are fan-out stages: one run emits N artifacts, one per scene. Treat each as a single `StageStatus` entry (status transitions apply to the stage as a unit, not per scene), but iterate the per-stage protocol internally for each `scene_id` in `03_storyboard.json.scenes`:

**`script` fan-out:**

- Pre-flight: validate `03_storyboard.json` once before the loop.
- For each `scene_id` in storyboard order:
  - `mkdir -p artifacts/<job_id>/scenes/<scene_id>/`.
  - Invoke the `script` agent for that `scene_id`. The agent writes only `scenes/<scene_id>/script.json`.
  - Validate: `uv run pedagogica-tools validate Script artifacts/<job_id>/scenes/<scene_id>/script.json`. Same retry/fail rules as scalar stages — one retry per scene, second failure halts the whole stage.
  - Run:
    ```
    uv run pedagogica-tools check-script artifacts/<job_id>/scenes/<scene_id>/script.json artifacts/<job_id>/03_storyboard.json
    ```
    - Exit 0 → continue.
    - Exit 1 on `word_budget` → re-prompt the script agent once with the failing report. Second failure halts the stage.
    - Warn-only (`quotas_met < 5`) → log to trace, do **not** halt.
    - Exit 2 (usage/IO) → hard fail.
- Mark the stage `complete` only after every scene's script is validated. `artifact_path` for a fan-out stage is the **directory**: `"scenes/"`.

**`chalk-code` fan-out (includes compile + repair loop):**

- Pre-flight: validate `03_storyboard.json` once; validate each scene's `scenes/<scene_id>/script.json` before working on it.
- For each `scene_id` in storyboard order:
  1. **Codegen (attempt 1).** Invoke the `chalk-code` agent. The agent writes `scenes/<scene_id>/code.py` and `scenes/<scene_id>/code.json`. Validate the `code.json`:
     `uv run pedagogica-tools validate ChalkCode artifacts/<job_id>/scenes/<scene_id>/code.json`. On validation failure: one re-prompt with stderr; second failure halts the stage.
  2. **Compile.** Run:
     ```
     uv run pedagogica-tools chalk-render \
       artifacts/<job_id>/scenes/<scene_id>/code.py \
       <scene_class_name> \
       artifacts/<job_id>/scenes/<scene_id>/<scene_id>.mp4 \
       --scene-id <scene_id> --attempt 1 \
       --result-json artifacts/<job_id>/scenes/<scene_id>/compile_attempt_1.json
     ```
     - Exit 0 (render succeeded) → the scene's `.mp4` exists; go to the next scene.
     - Exit 1 (compile failed) → enter the repair loop.
  3. **Repair loop (up to 3 total compile attempts including the first).** For attempt `N` in `{2, 3}`:
     - Invoke the `chalk-repair` agent with the failing `code.py` and `compile_attempt_<N-1>.json`. Agent overwrites `code.py` and writes a new `code.json` (producer `chalk-repair`). Validate the new `code.json` as in step 1.
     - Re-run `chalk-render` with `--attempt N` and `--result-json compile_attempt_<N>.json`. On exit 0 → scene done. On exit 1 at `N=3` → mark the whole stage `failed` and halt.
  4. Every `compile_attempt_<N>.json` must validate against `CompileResult` — the render helper writes it; don't hand-edit. No separate validation step is needed (the helper emits schema-conforming JSON).
- Mark the stage `complete` only after every scene has a successful render.
- `artifact_path = "scenes/"` (directory, same convention as `script`).
- **Post-render duration-drift check (warn-only):** before marking the stage complete, run
  ```
  uv run pedagogica-tools check-duration artifacts/<job_id>
  ```
  (no `--strict`). The tool reads the latest `compile_attempt_<N>.json` per scene and reports `|video_duration - target_duration| / target` drift. Surface the stdout table in the stage's `trace` event so `pedagogica-tools view` shows which scenes are off-target. Do **not** halt the stage on drift in Phase 1 — drift is a quality signal, not a failure. If a scene is >15 % off, the fix belongs in `chalk-code` SKILL (AnimationGroup `lag_ratio` accounting, per `workflows/lessons.md`), not in per-scene hand-patches.

**`tts` fan-out (per-scene, non-LLM):**

- Pre-flight: validate each scene's `scenes/<scene_id>/script.json` before working on it. Validate `03_storyboard.json` once up front to read `voice_id`.
- `voice_id` comes from `03_storyboard.json.voice_id` (storyboard agent pins it; Rachel = `21m00Tcm4TlvDq8ikWAM` by default).
- For each `scene_id` in storyboard order:
  1. `mkdir -p artifacts/<job_id>/scenes/<scene_id>/audio/`.
  2. Write `script.text` verbatim to `artifacts/<job_id>/scenes/<scene_id>/audio/narration.txt` (the TTS tool takes a file path, not a string).
  3. Invoke:
     ```
     uv run pedagogica-tools elevenlabs-tts \
       artifacts/<job_id>/scenes/<scene_id>/audio/narration.txt \
       <voice_id> \
       artifacts/<job_id>/scenes/<scene_id>/audio/clip.mp3 \
       --scene-id <scene_id> \
       --result-json artifacts/<job_id>/scenes/<scene_id>/audio/clip.json
     ```
     - Exit 0 → continue.
     - Exit 1 (API / IO error) → retry once; second failure halts the stage.
     - Exit 2 (usage error) → hard fail.
  4. Validate: `uv run pedagogica-tools validate AudioClip artifacts/<job_id>/scenes/<scene_id>/audio/clip.json`. One retry on validation failure; second failure halts.
- Mark stage `complete` only after every scene has a validated `clip.json`. `artifact_path = "scenes/"`.
- Do not override `--model-id` or voice params unless the storyboard's `style_hints` demand it — Rachel + `eleven_multilingual_v2` is the locked default.

**`sync` fan-out (per-scene agent):**

- Pre-flight: validate `scenes/<scene_id>/script.json` and `scenes/<scene_id>/audio/clip.json` for every scene before entering the loop.
- For each `scene_id` in storyboard order:
  - Invoke the `sync` agent. The agent writes only `scenes/<scene_id>/sync.json`.
  - Validate: `uv run pedagogica-tools validate SyncPlan artifacts/<job_id>/scenes/<scene_id>/sync.json`. One retry with stderr; second failure halts the stage.
- Mark stage `complete` only after every scene has a validated `sync.json`. `artifact_path = "scenes/"`.

### `editor` (whole-job, non-LLM)

- Pre-flight: confirm every scene has `<scene_id>.mp4` (from chalk-code) and `audio/clip.mp3` and `sync.json`. Missing inputs → halt with the scene id.
- Invoke once for the whole job:
  ```
  uv run pedagogica-tools ffmpeg-mux artifacts/<job_id> --output final.mp4
  ```
  - Default crossfade `0.0` seconds (no crossfades in Phase 1 unless a storyboard hint asks for one).
  - Exit 0 → confirm `artifacts/<job_id>/final.mp4` exists and is non-empty.
  - Exit 1 → one retry with `--force`; second failure halts the stage.
- No JSON schema to validate — the tool emits mp4 only. Orchestrator only checks `final.mp4` was written and `ffprobe` reports a non-zero duration (done inside the mux tool; orchestrator just checks exit code).
- `artifact_path = "final.mp4"`.

### `subtitle` (whole-job, non-LLM)

- Pre-flight: confirm every scene has `audio/clip.json` (word_timings source). Missing → halt.
- Invoke once for the whole job:
  ```
  uv run pedagogica-tools subtitle-gen artifacts/<job_id>
  ```
  - Exit 0 → confirm `artifacts/<job_id>/captions.vtt` and `captions.srt` exist.
  - Exit 1 → one retry with `--force`; second failure halts.
- No JSON schema to validate — sidecars only. Never burn captions into video (memory: captions opt-in sidecar).
- `artifact_path = "captions.vtt"`.

## Failure handling

- **Validation failure (after 1 retry):** mark the stage `failed`, set `current_stage = null`, persist `job_state.json`, halt. Do not advance. Do not delete the bad artifact — leave it so the user can inspect.
- **Unexpected error:** same as above. `job_state.json` must always remain parseable by `JobState`.
- **Sandbox violation / cost-cap hit:** the `chalk-render` helper runs chalk inside `sandbox-exec` (macOS). A sandbox violation surfaces as `CompileResult.error_classification = "sandbox_violation"` — treat the scene's compile as failed and enter the repair loop; if repair keeps tripping the sandbox, halt the stage with a hard fail. Do **not** disable sandboxing. TTS cost caps live in `pedagogica-tools elevenlabs-tts`, outside this tier.

## End-of-tier handoff

When `subtitle` completes:

- `current_stage = null`.
- `terminal = true` (Phase 1 tier is the full pipeline — there is no later tier in this worktree).
- `final_artifact_paths` is populated with at minimum:
  - `"video": "final.mp4"`
  - `"captions_vtt": "captions.vtt"`
  - `"captions_srt": "captions.srt"`
- Rewrite and re-validate `job_state.json` a final time.
- Print: job id, path to `03_storyboard.json`, per-scene `script.json` / `code.py` / `<scene_id>.mp4` / `audio/clip.json` / `sync.json` paths, job-level `final.mp4` + `captions.vtt` + `captions.srt` paths, scene count, total narrated duration (sum of per-scene `clip.total_duration_seconds`), and per-scene compile-attempt counts (1/2/3).

If the stage halted earlier (failed), `terminal` stays `false`, `current_stage = null`, and the last non-complete stage carries `status = "failed"`. `/pedagogica resume` can re-enter from the failed stage once the upstream issue is fixed.

## Hard rules

- Non-LLM work is always `uv run pedagogica-tools <sub>`; never reimplement.
- Never hand-edit `artifacts/` outside the protocol above.
- Never parse JSON for validation purposes — always shell to `pedagogica-tools validate`.
- Never skip a stage. All nine Phase-1 stages are active; each must reach `complete` before the next starts.
- Never invent a `job_id`; it comes from `/pedagogica`.
