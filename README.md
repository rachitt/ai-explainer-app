# Pedagogica

AI pipeline that turns a learning objective into an explainer video. Manim for visuals, ElevenLabs for narration, Claude Code as the Phase 1 runtime — no Anthropic API key required.

**Status:** Phase 1 in progress (weeks 1–6). Calculus only, CLI only, single English narrator, 2–4 min videos. See `docs/ROADMAP.md`.

## Getting started

If you're working in this repo, read `CLAUDE.md` first. Then `workflows/lessons.md`.

## Documentation

- `CLAUDE.md` — project orientation + conventions
- `docs/ARCHITECTURE.md` — runtime, agent DAG, schemas, sandbox, observability
- `docs/SKILLS.md` — skill format + full inventory + agent-to-skill mapping
- `docs/ROADMAP.md` — phase-by-phase plan with Phase 1 weekly breakdown
- `docs/RISKS.md` — top risks, early-warning signals, kill criteria
- `docs/NON_GOALS.md` — what we're deliberately not building
- `workflows/lessons.md` — append-only log of past mistakes

## License

Apache 2.0. Private through Phase 5; public cut at Phase 6.
