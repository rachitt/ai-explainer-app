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

| Stage | Agent skill | Output artifact | Output schema |
|---|---|---|---|
| intake | `agents/intake/SKILL.md` | `01_intake.json` | `IntakeResult` |
| curriculum | `agents/curriculum/SKILL.md` | `02_curriculum.json` | `CurriculumPlan` |
| storyboard | `agents/storyboard/SKILL.md` | `03_storyboard.json` | `Storyboard` |

Stages beyond `storyboard` (script, visual-planner, layout, manim-code, compile, tts, sync, editor, subtitle, critics) are **not** delivered in this worktree. If `job_state.stages` lists them, leave them `pending` and exit cleanly after `storyboard`.

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

## Failure handling

- **Validation failure (after 1 retry):** mark the stage `failed`, set `current_stage = null`, persist `job_state.json`, halt. Do not advance. Do not delete the bad artifact — leave it so the user can inspect.
- **Unexpected error:** same as above. `job_state.json` must always remain parseable by `JobState`.
- **Sandbox violation / cost-cap hit:** not reachable in the planning tier (no Manim / TTS here). If you somehow encounter one, halt immediately.

## End-of-tier handoff

When `storyboard` completes:

- `current_stage` is set to `null` (Phase 1 planning tier end).
- `terminal` stays `false` — later tiers will flip it.
- Print the path to `03_storyboard.json` and summarize scene count + total duration.

## Hard rules

- Non-LLM work is always `uv run pedagogica-tools <sub>`; never reimplement.
- Never hand-edit `artifacts/` outside the protocol above.
- Never parse JSON for validation purposes — always shell to `pedagogica-tools validate`.
- Never skip a stage. Phase-1 tiers beyond `storyboard` are inactive, not skippable.
- Never invent a `job_id`; it comes from `/pedagogica`.
