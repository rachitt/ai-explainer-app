---
name: pedagogica
description: Generate, resume, or inspect a Pedagogica explainer video job
argument-hint: <generate|resume|view> <args...>
---

# /pedagogica

Entry point for the Pedagogica pipeline. Dispatches to the orchestrator skill under `pedagogica/skills/agents/orchestrator/`.

## Subcommands

- `generate <prompt>` — run the full pipeline for a learning objective. Creates a new `artifacts/<job_id>/` directory and walks the agent DAG from intake to final MP4.
- `resume <job_id>` — resume an existing job from its first non-complete stage. Reads `artifacts/<job_id>/job_state.json` to find the resume point.
- `view <job_id>` — print the timeline, costs, and skill versions for a job. Shells out to `pedagogica-tools view`.

## Arguments

$ARGUMENTS

## Notes

This command is a thin dispatcher. Real orchestration logic lives in the orchestrator agent skill (delivered in the `skills/agents-planning` worktree during Week 1).

Non-LLM work (Manim render, ElevenLabs HTTP, FFmpeg, trace appends, schema validation) is invoked via `uv run pedagogica-tools <subcommand>` — never reimplemented inline.
