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

Stages beyond `script` (chalk-code, chalk-repair, sync, editor, subtitle, critics) are **not** delivered in this worktree. If `job_state.stages` lists them, leave them `pending` and exit cleanly after `script`.

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

`script` is a fan-out stage: one run emits N artifacts, one per scene. Treat the whole stage as a single `StageStatus` entry (status transitions apply to the stage as a unit, not per scene), but iterate the per-stage protocol internally for each `scene_id` in `03_storyboard.json.scenes`:

- Pre-flight: validate `03_storyboard.json` once before the loop.
- For each `scene_id` in storyboard order:
  - `mkdir -p artifacts/<job_id>/scenes/<scene_id>/`.
  - Invoke the `script` agent for that `scene_id`. The agent writes only `scenes/<scene_id>/script.json`.
  - Validate: `uv run pedagogica-tools validate Script artifacts/<job_id>/scenes/<scene_id>/script.json`. Same retry/fail rules as scalar stages — one retry per scene, second failure halts the whole stage.
- Mark the stage `complete` only after every scene's script is validated. `artifact_path` for a fan-out stage is the **directory**: `"scenes/"`.

## Failure handling

- **Validation failure (after 1 retry):** mark the stage `failed`, set `current_stage = null`, persist `job_state.json`, halt. Do not advance. Do not delete the bad artifact — leave it so the user can inspect.
- **Unexpected error:** same as above. `job_state.json` must always remain parseable by `JobState`.
- **Sandbox violation / cost-cap hit:** not reachable in the planning + script tier (no chalk / TTS here). If you somehow encounter one, halt immediately.

## End-of-tier handoff

When `script` completes:

- `current_stage` is set to `null` (Phase 1 planning+script tier end).
- `terminal` stays `false` — later tiers (chalk-code, chalk-repair, sync, editor) will flip it.
- Print the path to `03_storyboard.json`, the per-scene `scenes/<scene_id>/script.json` paths, scene count, and total duration.

## Hard rules

- Non-LLM work is always `uv run pedagogica-tools <sub>`; never reimplement.
- Never hand-edit `artifacts/` outside the protocol above.
- Never parse JSON for validation purposes — always shell to `pedagogica-tools validate`.
- Never skip a stage. Phase-1 tiers beyond `script` are inactive, not skippable.
- Never invent a `job_id`; it comes from `/pedagogica`.
