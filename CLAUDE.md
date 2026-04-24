# Pedagogica

**First thing every session: read `workflows/lessons.md`.** Append-only log of past mistakes — don't repeat them.

**Second: read `docs/CHALK_QUALITY_GAP.md`.** Honest accounting of where chalk output quality lags manim and the ordered P0–P6 backlog to close the gap. Every chalk PR must either close one of those items or explain why it doesn't. Single most important doc for raising video quality.

## What this is

An AI pipeline that turns a learning objective ("explain derivatives to calc 1 students") into a narrated explainer video in the style of 3Blue1Brown / Khan Academy. Core bet: LLMs generate **chalk** code (this repo's own renderer, under `chalk/`) → render → overlay ElevenLabs TTS with word-level sync. No generative video models for pedagogical content.

chalk replaced Manim Community Edition as the visual primitive on 2026-04-21. Rationale, kill criteria, and reversion plan live in `docs/adr/0001-chalk-replaces-manim.md`; phased primitive plan in `docs/CHALK_ROADMAP.md`. Scene authoring rules in `chalk/CLAUDE.md`.

Full spec: `docs/ARCHITECTURE.md`, `docs/SKILLS.md`, `docs/ROADMAP.md`, `docs/RISKS.md`, `docs/NON_GOALS.md`, `docs/CHALK_ROADMAP.md`, `docs/CHALK_QUALITY_GAP.md`.

## Phase 1 scope (now)

- **Runtime:** Claude Code plugin (`/pedagogica` slash command + skills). Zero Anthropic-API cost — runs on the user's Claude Code subscription.
- **Domain:** calculus only. 2–4 minute videos, 720p, single English narrator, ElevenLabs TTS.
- **Target:** 10 calculus topics, 8+ watchable, in 6 weeks.
- **Persistence:** filesystem only, under `./artifacts/<job_id>/`. No DB.
- **Sandbox:** macOS `sandbox-exec` for chalk execution.

## Non-negotiables

- **chalk** (this repo's own renderer) is the visual primitive. No Manim/SVG/Motion Canvas/Remotion detours. See `docs/adr/0001-chalk-replaces-manim.md` for why and `docs/CHALK_ROADMAP.md` for what ships when. Kill criteria in the ADR are the only path back to Manim CE.
- **No generative video** (Sora/Veo/Runway/Kling) for pedagogical content — they can't keep equations consistent.
- **No Anthropic API key usage in Phase 1.** Everything goes through Claude Code.
- **No WhisperX in Phase 1.** ElevenLabs returns word timings natively; use that.
- **All LLM-generated code runs sandboxed.** Never `exec()` / `eval()` model output. Ever.
- **Pydantic-validated messages** between agents. No free-form JSON parsing.
- **Content-hash LLM cache on from day 1.** Re-runs must be cache hits.

## Runtime model

Pipeline = **8 agent skills** + **10 knowledge skills** (roster settled 2026-04-22 after the 33 → trim; the rest were stale or merged in). Inter-agent messages = JSON files on disk under `artifacts/<job_id>/`, validated against Pydantic schemas in `schemas/`. Non-LLM work (chalk render, FFmpeg, ElevenLabs HTTP) = Python helpers in `tools/`, invoked via Bash as `uv run pedagogica-tools <subcommand>`.

### Agent skills (`pedagogica/skills/agents/`)

`orchestrator` → `intake` → `curriculum` → `storyboard` → `script` → `chalk-code` → `chalk-repair` → `sync`

- `orchestrator` coordinates stages
- `intake` normalizes raw user prompt → typed IntakeResult (topic, domain, audience, length)
- `curriculum` breaks topic into beats
- `storyboard` plans visual arc per scene
- `script` writes narration (absorbs pacing + spoken-style rules inline)
- `chalk-code` generates chalk Python (absorbs visual-planner beat→op mapping)
- `chalk-repair` fixes failing chalk code (uses `chalk-debugging`)
- `sync` TTS + word-timing + FFmpeg mux (absorbs audio-visual-sync + tts-prompting)

### Knowledge skills (`pedagogica/skills/knowledge/`, also symlinked under `.claude/skills/` so Claude Code auto-discovers them for direct invocation)

- `chalk-primitives` — canonical chalk API reference (chalk-code reads)
- `chalk-calculus-patterns` — Riemann / chain-rule / FTC templates
- `chalk-circuit-patterns` — Wire(breaks=[...]) + component conventions
- `chalk-physics-patterns` — projectile, pendulum, spring-mass, FBD templates
- `chalk-chemistry-patterns` — bond / molecule / reaction-mechanism templates
- `chalk-coding-patterns` — code-trace, call-stack, tree-search templates
- `chalk-graph-patterns` — hand-placed node layouts, Dijkstra templates
- `chalk-debugging` — chalk-repair reads this
- `scene-spec-schema` — SceneSpec mental model (no on-disk spec.json in Phase 1, but the contract still informs the element → animation decomposition)
- `latex-for-video` — MathTex + pdflatex gotchas

### How skills are invoked

- **Claude (interactive)** — use the `Skill` tool with the skill name when work matches it (e.g. `Skill(skill="chalk-primitives")` before writing a scene).
- **Codex (delegated work)** — briefs explicitly reference the skill path: e.g. "Read `pedagogica/skills/knowledge/chalk-circuit-patterns/SKILL.md` first before editing circuits code". Codex has no auto-discovery; paths must be explicit.
- **Pedagogica runtime (Phase 1 goal)** — agents declare `requires:` in their SKILL.md frontmatter; the orchestrator loads them on stage start.

## Repo layout

```
chalk/            the visual primitive — library, CLAUDE.md authoring rules, examples, tests
pedagogica/       Claude Code plugin — agent skills + knowledge skills + domain packs
schemas/          Pydantic models for inter-agent messages (uv workspace package)
tools/            Python helpers: chalk_render, elevenlabs_tts, ffmpeg_mux, trace, job_view
sandbox/          sandbox-exec profiles for chalk isolation
docs/             ARCHITECTURE / SKILLS / ROADMAP / RISKS / NON_GOALS / CHALK_ROADMAP + adr/
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
- Do not relitigate the chalk bet mid-phase. Use the kill criteria in `docs/adr/0001-chalk-replaces-manim.md` (K1–K5) and `RISKS.md` R1.

## When you correct a mistake

Append to `workflows/lessons.md`. Format: **Mistake / Root cause / Fix / Applies to**. Keep entries ≤8 lines. No silent fixes — the log is the whole point.

## Where to find more

- Architectural decisions → `docs/ARCHITECTURE.md` (runtime, DAG, schemas, persistence, sandbox, observability)
- chalk (visual primitive) → `docs/adr/0001-chalk-replaces-manim.md` for the decision, `docs/CHALK_ROADMAP.md` for the phased plan, `chalk/CLAUDE.md` for scene-authoring rules
- Skill authoring → `pedagogica/skills/AUTHORING.md` (created week 1)
- Phase plan → `docs/ROADMAP.md` (week-by-week for Phase 1; milestones beyond)
- What we're NOT building → `docs/NON_GOALS.md`
- ADRs for major decisions → `docs/adr/`
