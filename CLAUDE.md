# Pedagogica

**First thing every session: read `workflows/lessons.md`.** Append-only log of past mistakes — don't repeat them.

## What this is

An AI pipeline that turns a learning objective ("explain derivatives to calc 1 students") into a narrated explainer video in the style of 3Blue1Brown / Khan Academy. Core bet: LLMs generate Manim Community Edition code → render → overlay ElevenLabs TTS with word-level sync. No generative video models for pedagogical content.

Full spec: `docs/ARCHITECTURE.md`, `docs/SKILLS.md`, `docs/ROADMAP.md`, `docs/RISKS.md`, `docs/NON_GOALS.md`.

## Phase 1 scope (now)

- **Runtime:** Claude Code plugin (`/pedagogica` slash command + skills). Zero Anthropic-API cost — runs on the user's Claude Code subscription.
- **Domain:** calculus only. 2–4 minute videos, 720p, single English narrator, ElevenLabs TTS.
- **Target:** 10 calculus topics, 8+ watchable, in 6 weeks.
- **Persistence:** filesystem only, under `./artifacts/<job_id>/`. No DB.
- **Sandbox:** macOS `sandbox-exec` for Manim execution.

## Non-negotiables

- **Manim Community `0.19.x`** is the visual primitive. No SVG/Motion Canvas/Remotion detours.
- **No generative video** (Sora/Veo/Runway/Kling) for pedagogical content — they can't keep equations consistent.
- **No Anthropic API key usage in Phase 1.** Everything goes through Claude Code.
- **No WhisperX in Phase 1.** ElevenLabs returns word timings natively; use that.
- **All LLM-generated code runs sandboxed.** Never `exec()` / `eval()` model output. Ever.
- **Pydantic-validated messages** between agents. No free-form JSON parsing.
- **Content-hash LLM cache on from day 1.** Re-runs must be cache hits.

## Runtime model

Each of the 22 agents in the spec = a Claude Code skill under `pedagogica/skills/agents/<name>/`. Inter-agent messages = JSON files on disk under `artifacts/<job_id>/`, validated against Pydantic schemas in `schemas/`. Non-LLM work (Manim render, FFmpeg, ElevenLabs HTTP) = Python helpers in `tools/`, invoked via Bash from skills as `uv run pedagogica-tools <subcommand>`.

## Repo layout

```
pedagogica/       Claude Code plugin — agent skills + knowledge skills + domain packs
schemas/          Pydantic models for inter-agent messages (uv workspace package)
tools/            Python helpers: manim_render, elevenlabs_tts, ffmpeg_mux, trace, job_view
sandbox/          sandbox-exec profiles for Manim isolation
docs/             ARCHITECTURE / SKILLS / ROADMAP / RISKS / NON_GOALS
tests/            regression (10 calculus topics) + integration
workflows/        lessons.md — append-only mistake log
artifacts/        per-job state, gitignored
```

## How to run (post-scaffold)

```
uv sync                                        # install workspace deps
/pedagogica generate "explain chain rule"      # from a Claude Code session
pedagogica-tools view <job_id>                 # timeline, costs, skill versions
uv run pytest tests/regression                 # full Phase 1 suite (~30 min)
```

## Commit conventions

- **Short, one-line subject.** No trailing period. Present tense (`add …`, `fix …`, `pin …`). Body only when a change needs justification that can't fit in the subject.
- **No Anthropic / Claude co-authored-by trailers.** Ever. Not in subject, not in body, not in squashed merges.
- **No emoji in commit messages.**
- **Scope prefix optional** but useful: `skills: add manim-calculus-patterns`, `tools: harden sandbox-exec profile`.
- **One logical change per commit.** Don't mix refactor + feature + config.
- **Git remotes are SSH** (`git@github.com:…`). Never HTTPS.

## Do NOT

- Do not add features outside the current phase's milestone scope. See `docs/ROADMAP.md`.
- Do not skip pre-commit hooks, tests, or signing with `--no-verify` / `--no-gpg-sign`.
- Do not merge a skill whose examples haven't been rendered and reviewed.
- Do not edit `artifacts/` by hand — it's generated state.
- Do not commit `.env`, credentials, ElevenLabs API keys, or rendered test videos.
- Do not introduce a new LLM provider without updating `tools/src/pedagogica_tools/llm/` abstractions.
- Do not relitigate the Manim bet mid-phase. Use `RISKS.md` R1 kill criteria.

## When you correct a mistake

Append to `workflows/lessons.md`. Format: **Mistake / Root cause / Fix / Applies to**. Keep entries ≤8 lines. No silent fixes — the log is the whole point.

## Where to find more

- Architectural decisions → `docs/ARCHITECTURE.md` (runtime, DAG, schemas, persistence, sandbox, observability)
- Skill authoring → `pedagogica/skills/AUTHORING.md` (created week 1)
- Phase plan → `docs/ROADMAP.md` (week-by-week for Phase 1; milestones beyond)
- What we're NOT building → `docs/NON_GOALS.md`
- ADRs for major decisions → `docs/adr/`
