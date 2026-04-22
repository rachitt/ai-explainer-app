---
name: pedagogica
description: Generate, resume, or inspect a Pedagogica explainer video job
argument-hint: <generate|resume|view> <args...>
---

# /pedagogica

Entry point for the Pedagogica pipeline. Parse `$ARGUMENTS`, dispatch to the right flow, and return a pointer to the job directory. Non-LLM work is **always** `uv run pedagogica-tools <subcommand>`; never reimplement it inline.

Arguments: `$ARGUMENTS`

---

## Dispatch

Split `$ARGUMENTS` on whitespace. The first token is the subcommand.

### `generate <prompt...>`

Fresh pipeline run for a learning objective.

1. Allocate `job_id` = a new UUIDv4. Let `JOB_DIR = artifacts/<job_id>/`.
2. Create `JOB_DIR` (and parents if missing).
3. Write the initial `JOB_DIR/job_state.json` with:
   - Trace metadata: `trace_id = <fresh UUIDv4>`, `span_id = <fresh UUIDv4>`, `parent_span_id = null`, `timestamp = <now-UTC-ISO8601>`, `producer = "orchestrator"`, `schema_version = "0.0.1"`.
   - `job_id = <the UUID>`, `created_at = <now>`, `user_prompt = "<prompt joined>"`.
   - `skills_pinned = {}`, `models_default = {}`, `final_artifact_paths = {}`, `terminal = false`.
   - `current_stage = "intake"`.
   - `stages`: exactly these five `StageStatus` entries for the Phase-1 planning + script + render tier, all `status = "pending"`:
     - `{"name": "intake", "status": "pending"}`
     - `{"name": "curriculum", "status": "pending"}`
     - `{"name": "storyboard", "status": "pending"}`
     - `{"name": "script", "status": "pending"}`
     - `{"name": "chalk-code", "status": "pending"}`
4. Validate the initial job state:
   ```
   uv run pedagogica-tools validate JobState artifacts/<job_id>/job_state.json
   ```
   Non-zero exit = abort without touching anything else.
5. Load the `orchestrator` skill (`pedagogica/skills/agents/orchestrator/SKILL.md`) in mode `start` with `job_id`. The orchestrator walks `intake → curriculum → storyboard → script → chalk-code`, invoking each agent skill and validating every emitted artifact. `script` and `chalk-code` are per-scene fan-out stages — one `scenes/<scene_id>/script.json`, `code.py`, `code.json`, and `<scene_id>.mp4` per storyboard scene. The `chalk-code` stage includes render via `pedagogica-tools chalk-render` with up to 3 compile attempts (chalk-repair takes attempts 2 and 3).
6. On success, report: job id, path to `03_storyboard.json`, per-scene script + render paths, scene count, total duration, and per-scene compile-attempt counts. Note that sync / editor / subtitle tiers are not wired yet (subsequent worktrees).

### `resume <job_id>`

Continue a previously interrupted job.

1. Verify `artifacts/<job_id>/job_state.json` exists. If not, error and exit.
2. Validate it: `uv run pedagogica-tools validate JobState artifacts/<job_id>/job_state.json`. Non-zero = abort.
3. Load the `orchestrator` skill in mode `resume` with `job_id`. It picks the first non-`complete` stage and proceeds.

### `view <job_id>`

Shell out; do not re-implement:

```
uv run pedagogica-tools view <job_id>
```

Print the tool's stdout verbatim.

### `validate <Schema> <path>`

Convenience passthrough:

```
uv run pedagogica-tools validate <Schema> <path>
```

---

## Hard rules

- Never hand-edit `artifacts/`. The orchestrator is the only writer inside a job directory, and it writes only per the protocol in its `SKILL.md`.
- Every stage transition ends with a `pedagogica-tools validate <Schema> <path>` call. Non-zero exit is a hard failure; the orchestrator persists `job_state.json` consistently and halts.
- LLM-generated Python code (Manim) is out of scope for this tier. If you encounter it, you are in the wrong worktree.
- Do not invent schema names; the registry lives at `schemas/src/pedagogica_schemas/registry.py`. Run `uv run pedagogica-tools list-schemas` to see what's available.
