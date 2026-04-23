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

| Stage | Agent skill | Output artifact | Output schema | Fan-out |
|---|---|---|---|---|
| intake | `agents/intake/SKILL.md` | `01_intake.json` | `IntakeResult` | once per job |
| curriculum | `agents/curriculum/SKILL.md` | `02_curriculum.json` | `CurriculumPlan` | once per job |
| storyboard | `agents/storyboard/SKILL.md` | `03_storyboard.json` | `Storyboard` | once per job |
| script | `agents/script/SKILL.md` | `scenes/<scene_id>/script.json` | `Script` | once per scene in `storyboard.scenes` |
| chalk-code | `agents/chalk-code/SKILL.md` (+ `agents/chalk-repair/SKILL.md` on failure) | `scenes/<scene_id>/code.py` + `code.json` + `scene_<N>.mp4` | `ChalkCode` (for `code.json`); `CompileResult` (for each `compile_attempt_<N>.json`) | once per scene; includes render + up to 3 repair attempts |

Stages beyond `chalk-code` (sync, editor, subtitle, critics) are **not** delivered in this worktree. If `job_state.stages` lists them, leave them `pending` and exit cleanly after `chalk-code`.

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

## Failure handling

- **Validation failure (after 1 retry):** mark the stage `failed`, set `current_stage = null`, persist `job_state.json`, halt. Do not advance. Do not delete the bad artifact — leave it so the user can inspect.
- **Unexpected error:** same as above. `job_state.json` must always remain parseable by `JobState`.
- **Sandbox violation / cost-cap hit:** the `chalk-render` helper runs chalk inside `sandbox-exec` (macOS). A sandbox violation surfaces as `CompileResult.error_classification = "sandbox_violation"` — treat the scene's compile as failed and enter the repair loop; if repair keeps tripping the sandbox, halt the stage with a hard fail. Do **not** disable sandboxing. TTS cost caps live in `pedagogica-tools elevenlabs-tts`, outside this tier.

## End-of-tier handoff

When `chalk-code` completes:

- `current_stage` is set to `null` (Phase 1 planning + script + render tier end).
- `terminal` stays `false` — later tiers (sync, editor, subtitle) will flip it.
- Print: path to `03_storyboard.json`, the per-scene `scenes/<scene_id>/script.json` paths, the per-scene `scenes/<scene_id>/<scene_id>.mp4` renders, scene count, total duration, and a per-scene compile-attempt count (1/2/3).

## Hard rules

- Non-LLM work is always `uv run pedagogica-tools <sub>`; never reimplement.
- Never hand-edit `artifacts/` outside the protocol above.
- Never parse JSON for validation purposes — always shell to `pedagogica-tools validate`.
- Never skip a stage. Phase-1 tiers beyond `chalk-code` are inactive, not skippable.
- Never invent a `job_id`; it comes from `/pedagogica`.
