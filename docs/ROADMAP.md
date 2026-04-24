# Pedagogica — Roadmap (Artifact 4)

Status: Phase 1 week-by-week detailed. Phases 2–6 milestones + kill criteria.

> **Renderer update (2026-04-21):** References to Manim / MCE are superseded by **chalk** per ADR 0001. Skill names `manim-primitives`, `manim-calculus-patterns`, `manim-<domain>-patterns` are renamed `chalk-*`. chalk's own phased plan lives in `docs/CHALK_ROADMAP.md` and its milestones must land alongside the domain milestones here (e.g. chalk C1 parity floor must complete before pedagogica M1.6).

This is the delivery plan. Every phase ends with a working, demonstrable system. Phase 1 is planned at the week level; later phases at the milestone level.

---

## 1. Principles

- **Ship each phase to real users before starting the next.** "Real user" = at minimum Rachit himself evaluating against the rubric; ideally external beta users by Phase 4.
- **Milestone = demonstrable.** No phase is "done" until the demo reproduces on a clean clone of the repo.
- **Kill criteria are real.** If a phase breaches them, we pivot or stop. The alternative is a year-long project that doesn't ship.
- **Parallelism via worktrees.** Where a week lists multiple independent artifacts, expect parallel worktrees.
- **Lessons log (`workflows/lessons.md`) is appended every time the user corrects a mistake**. Never skipped.

---

## 2. Phase dependencies

```
Phase 1 (tracer bullet, calculus)
   │
   └─► Phase 2 (quality + critic loop) — needs Phase 1's DAG working end-to-end
           │
           └─► Phase 3 (multi-domain) — needs Phase 2's critic loop to catch domain regressions
                   │
                   └─► Phase 4 (web platform) — needs Phase 3's reliability for external users
                           │
                           └─► Phase 5 (scale) — needs Phase 4's platform for multi-user telemetry
                                   │
                                   └─► Phase 6 (ecosystem) — needs Phase 5's scale to attract third parties
```

Phases are strictly serial. No skipping; the inputs of Phase N require Phase N-1's outputs at quality.

---

## 3. Phase 1 — Tracer Bullet (weeks 1–6)

**Goal:** End-to-end calculus video generation from `/pedagogica generate "…"` to `final.mp4`. 2–4 min videos, 720p, one voice, English, ElevenLabs. 10 topics, 8+ watchable.

**Non-goals for Phase 1 (repeated from NON_GOALS.md):** critic-driven regeneration, scene-level regen, multi-language, multi-domain, music, SFX, brand kits, web UI, subtitles beyond basic VTT, WhisperX.

**Working mode:** solo + Claude Code in git worktrees off `main`.

### Week 1 — Scaffold + planning tier

**Input:** Approved Artifacts 1–6.

**Scope:**
- Repo init on `main`: `.gitignore`, `pyproject.toml` (uv workspace), `CLAUDE.md` (≤200 lines), `workflows/lessons.md`, `LICENSE` (Apache 2.0 placeholder — private repo still), `README.md` (minimal).
- `schemas/` package: all 10 top-tier Pydantic models from ARCHITECTURE §5 + base class.
- `tools/` package skeleton: `pedagogica-tools` CLI shell with `validate`, `trace`, `job-view` subcommands wired (others stubbed).
- `pedagogica/` Claude Code plugin: `plugin.json`, `/pedagogica` slash command file.
- Agent skills (planning tier): **intake**, **curriculum**, **storyboard**.
- Knowledge skills: `scene-spec-schema`, `pedagogy-sequencing`, `explanation-patterns`, `pedagogy-cognitive-load`, `color-and-typography` (minimal preset), `domain-calculus` (curriculum map + 20 canonical topics).
- Tests: smoke tests on schema round-trips; one end-to-end test that `/pedagogica generate "derivatives"` produces a valid `03_storyboard.json`.

**Output:** Command runs planning tier to completion; writes `01_intake.json`, `02_curriculum.json`, `03_storyboard.json` for any calculus topic. Storyboard contains 5–8 scene beats totaling 180–240s.

**Success criterion:** Valid storyboards produced for 5 trial calculus topics with zero validation errors. Token caching working (≥70% cache-read on second run of same topic).

**Risk flags:** If storyboards are shallow or incoherent (beats don't build on each other) after a week's iteration, pause and invest more in `pedagogy-sequencing` + `explanation-patterns` before moving on.

### Week 2 — Script + visual planner + layout

**Scope:**
- Agent skills: **script**, **visual-planner**, **layout**, **script-critic** (report-only stub).
- Knowledge skills: `spoken-narration-style`, `pacing-rules`, `scene-composition`.
- Expand `scene-spec-schema` content as visual planner needs reveal gaps.
- Integration: orchestrator walks planning → script → visual-planner → layout for each scene.

**Output:** For each scene in a storyboard, `script.json`, `spec.json`, `placements.json` are produced. All validate against schemas. No rendering yet.

**Success criterion:** 5 storyboards × ~6 scenes each = 30 scene specs produced, all schema-valid, all with non-trivial animation plans (≥3 animations per scene).

**Risk flags:** If SceneSpec is consistently under-specified (missing positions, ambiguous references), Layout agent is where we fix it — not by patching Visual Planner's output downstream.

### Week 3 — Manim codegen + sandbox + render

**Scope:**
- Knowledge skills: `manim-primitives` (15+ runnable examples), `manim-calculus-patterns` (10 canonical patterns), `latex-for-video`, `manim-debugging` (initial error catalog, ~8 entries).
- Agent skill: **manim-code** (Opus 4.7).
- Python tool: `pedagogica-tools manim-render`:
  - sandbox-exec profile in `sandbox/manim.sb`
  - resource limits (CPU/wall/memory/output size)
  - captures stderr → error_classification mapping
  - writes `render.mp4` on success
- Tests: render every `manim-primitives` + `manim-calculus-patterns` example in CI. Any failure blocks merge.
- Agent skill: **manim-repair** (Sonnet → Opus escalation per `retry-strategy`).

**Output:** For a single scene spec, `manim-code` generates `code.py`; `manim-render` produces `render.mp4`. Repair loop fires on compile errors.

**Success criterion:** First-pass compile success ≥ 40% across 30 scene specs from week 2. With repair loop (≤3 attempts): ≥ 75% eventual success.

**Risk flags:** This is the single riskiest week. If first-pass is <20% after aggressive skill iteration, reconsider whether the scene DSL is too permissive or the Manim skill library too thin. If repair loops converge <60%, the error catalog in `manim-debugging` is the first thing to expand.

### Week 4 — TTS + sync + end-to-end single scene

**Scope:**
- Python tool: `pedagogica-tools elevenlabs-tts`:
  - HTTP POST to Speech-Synthesis-with-Timestamps endpoint
  - Parses char-level timings → `WordTiming` list
  - Writes `clip.mp3` + `timing.json`
  - Cost-cap enforcement: per-job char quota (default 10 000 chars ≈ $2).
- Knowledge skills: `tts-prompting-elevenlabs` (voice selection, model ID, settings), `audio-visual-sync`.
- Agent skill: **sync**.
- Integration: for one scene end-to-end, run visual + audio tiers, produce `sync.json`.

**Output:** For a single scene, `scenes/scene_NN/{render.mp4, clip.mp3, timing.json, sync.json}` all produced; drift measurable via `pedagogica-tools measure-drift`.

**Success criterion:** Drift ≤ 0.15s on ≥ 80% of marker-anchored animations across 30 scenes. ElevenLabs call success rate ≥ 99%.

**Risk flags:** ElevenLabs timestamp endpoint has occasional gaps at utterance boundaries — watch for. If sync drift is consistently too high, the problem is usually the visual planner's `run_time` estimates — calibrate the rate constants in `manim-calculus-patterns`.

### Week 5 — Editor, subtitle, critic, full pipeline

**Scope:**
- Python tools: `ffmpeg_mux.py` (concatenate scenes + mux audio + apply 0.2s crossfade), `subtitle_gen.py` (WordTiming list → VTT / SRT).
- Agent skills: **editor**, **subtitle** (both near-deterministic, just orchestrate tool calls), **pedagogical-critic** (report-only).
- Knowledge skills: `pedagogical-critique` (rubric), `retry-strategy`, `cost-routing`, `budget-governance`.
- Integration: orchestrator runs the complete DAG. First full-length videos produced.
- Observability: `pedagogica-tools view <job_id>` prints timeline, costs, skills loaded, retries.

**Output:** `final.mp4` + `final.vtt` + `critique.json` for any calculus topic.

**Success criterion:** 3 full videos produced end-to-end, each watchable by Rachit's rubric, in <15 min wall-clock per video.

**Risk flags:** Editor transitions look choppy at scene boundaries is the most likely aesthetic defect — fix via crossfade durations and audio ducking at boundaries, not by elaborate transitions (those are Phase 2).

### Week 6 — Regression, hardening, demo

**Scope:**
- `tests/regression/`: 10 canonical calculus topics encoded as test fixtures.
  - Derivative as rate of change
  - Derivative as slope of tangent
  - Chain rule (intuition)
  - Product rule (visual proof)
  - Riemann sum → integral
  - Fundamental theorem of calculus (part 1)
  - Limits (ε-δ, concrete example)
  - Related rates (balloon inflating)
  - Optimization (box with max volume)
  - Area between curves
- Run the suite; count watchable. Iterate on worst 2.
- Bug-fix bash: whatever broke during the 10-topic run.
- Demo README with 3 rendered videos + transcript of the commands used.
- Update `workflows/lessons.md` with everything learned.

**Output:** Demo README, 10 rendered topics, regression suite green or yellow but documented.

**Success criterion:** ≥ 8 of 10 topics produce a watchable video (Rachit-judged, 5-point rubric from `pedagogical-critique`, threshold = 3.5).

**Risk flags:** If fewer than 6 of 10 are watchable, trigger the **Phase 1 kill criteria check** (§5).

### Phase 1 cumulative ship list

- 30 skills merged and tested.
- 14 agent skills functioning.
- `pedagogica-tools` CLI with 8 subcommands.
- Regression suite of 10 topics.
- Demo README + 3 uploadable videos.
- `CLAUDE.md` and `workflows/lessons.md` up to date.

---

## 4. Phases 2–6 — milestones

### Phase 2 — Quality and Robustness (weeks 7–12)

**Goal:** Phase 1's "sometimes watchable" becomes "reliably publication-quality."

**Milestones:**
- M2.1 (week 7–8): Manim first-pass compile ≥ 70%. Expand `manim-calculus-patterns` to 40 patterns. Gather failure catalog from Phase 1 regression runs; bake fixes into `manim-debugging`.
- M2.2 (week 9): Scene-level regeneration — edit one scene's script or spec and re-run just that scene. Requires orchestrator change to stage-resume at scene granularity.
- M2.3 (week 9–10): Visual Critic agent, wired blocking. Factual Verifier for math (SymPy-backed).
- M2.4 (week 10–11): Trace UI — `pedagogica-tools view --serve` launches local HTML waterfall.
- M2.5 (week 11–12): Cost dashboard — daily + per-job aggregations from `trace.jsonl`.

**Success criterion:** 20 calculus topics, 18+ publication-quality. End-to-end reliability ≥ 90% (job produces a final video without manual intervention).

### Phase 3 — Multi-Domain (weeks 13–20)

**Goal:** Prove the architecture generalizes.

**Milestones:**
- M3.1 (week 13–15): `domain-linear-algebra` + `manim-linalg-patterns`. Regression: 15 linalg topics.
- M3.2 (week 15–17): `domain-probability-statistics` + `manim-probability-patterns`. Regression: 15 probstat topics.
- M3.3 (week 17–19): `domain-classical-mechanics` + `manim-physics-patterns`. Regression: 15 mechanics topics.
- M3.4 (week 19–20): Alignment agent (WhisperX). Unlocks non-ElevenLabs TTS. Accessibility Auditor agent.
- Refinement: identify domain-agnostic patterns in pedagogy skills; factor out.

**Success criterion:** Across 4 domains × 15 topics = 60 regression runs, ≥ 80% publication-quality.

### Phase 4 — Web Platform (weeks 21–30)

**Goal:** Turn the engine into a product.

**Milestones:**
- M4.1 (week 21–22): Python service — FastAPI wrapping the pipeline. Postgres migrations from the filesystem layout. Redis job queue.
- M4.2 (week 22–23): Cloud render workers — Modal or Runpod for Manim sandbox (Firecracker-backed). Deprecate `sandbox-exec` in production.
- M4.3 (week 23–26): Next.js web app — create / review / iterate / publish flow. User accounts (Clerk or similar). Video library.
- M4.4 (week 26–27): Scene-level editor UI. Script-editing with auto-re-sync.
- M4.5 (week 27–28): Brand kits — palette/font/intro/outro upload. Applied via `color-and-typography` skill override.
- M4.6 (week 28–29): Public REST API + Python SDK. API-key auth. Per-user rate limits + budget caps.
- M4.7 (week 29–30): External beta — 20 users.

**Success criterion:** 20 beta users, NPS ≥ 40, 100+ videos generated through the platform, ≥ 85% reliability at scale.

### Phase 5 — Scale (weeks 31–40)

**Goal:** Category-defining capabilities.

**Milestones:**
- M5.1: Multi-language support (30+ languages). `spoken-narration-multilingual`, per-language voice pool, timing-preserving translation.
- M5.2: Series generation with cross-video consistency — reference resolver between videos, shared notation registry.
- M5.3: Voice cloning (ElevenLabs Professional Voice Clone) with consent-verified upload flow.
- M5.4: Interactive elements — pause-and-think prompts, embedded questions, comprehension-check mode.
- M5.5: Remaining domain packs + `manim-*-patterns` (algorithms, ML, chem, bio, econ).
- M5.6: 3D scene support (`manim-3d`, ManimGL integration).
- M5.7: Code execution visualizations (`manim-code-viz`).
- M5.8: Data viz from CSV/API inputs (`manim-data-viz`).
- M5.9: Template marketplace MVP.
- M5.10: TypeScript SDK. Partnerships with 2+ education platforms.

**Success criterion:** 500+ active users, 2+ partnership agreements signed.

### Phase 6 — Platform and Ecosystem (weeks 41+)

**Goal:** Become infrastructure others build on.

**Milestones:**
- M6.1: Open-source cut. Apache 2.0 on core. Contribution guide.
- M6.2: Self-hostable distribution — Terraform + Helm charts for core services.
- M6.3: Third-party domain pack SDK. Manifest format. First external pack shipped.
- M6.4: White-label offering (custom domain, brand, SSO) for edtech companies.
- M6.5: LMS integrations (SCORM, xAPI, LTI). Comprehension tracking ingestion.
- M6.6: Enterprise features — SSO, audit logs, content moderation, compliance (GDPR, FERPA).
- M6.7: Handwriting synthesis (`handwriting-synthesis`).

**Success criterion:** Ecosystem traction — ≥ 3 third-party domain packs published, ≥ 5 third-party integrations built.

---

## 5. Kill criteria (per phase)

If any of these conditions holds at the end of a phase, we pause and either pivot the approach or abandon the project. These are not "nice to avoid" — they are "if this happens we are building the wrong thing."

### Phase 1 kill criteria

- **Manim first-pass compile rate < 20%** after 4 weeks of aggressive skill investment.
  - *Why kill:* Means LLMs can't reliably generate Manim code even for calculus, the most LLM-friendly domain. The entire architectural bet is invalidated.
  - *Pivot if not killed:* Narrow the scene DSL so Manim-code becomes a template-fill rather than freeform codegen. Accept less expressive output.

- **Watchable rate < 50%** on the 10-topic regression at end of week 6.
  - *Why kill:* Pipeline runs, but output is junk. Could be pedagogy, visuals, audio, or sync; diagnose before pivoting.
  - *Pivot if not killed:* Hold scope, extend Phase 1 to 9 weeks, invest specifically in the dominant failure mode.

- **Wall-clock > 30 min per 3-min video** at end of week 6.
  - *Why kill:* Can't iterate fast enough to make Phase 2 investments learn-loop-compatible.
  - *Pivot:* Lower quality / resolution defaults. Investigate Manim render time — if FFmpeg mux is dominant, refactor.

- **ElevenLabs cost > $15 per 10-min video** at end of week 6.
  - *Why kill:* Makes the end-state cost target laughable and signals we're misusing TTS.
  - *Pivot:* Consolidate per-scene TTS calls into one; or switch voice model.

### Phase 2 kill criteria

- **Reliability stuck < 80%** after 6 weeks. → Architecture problem, not an iteration problem.
- **Critic agents produce noise, not signal** (regeneration triggered doesn't improve output). → Critic rubric is wrong.

### Phase 3 kill criteria

- **Linear algebra or probstat cannot clear 60% watchable** even after focused investment. → The pedagogy skills aren't as domain-agnostic as we assumed; pause for structural rework.

### Phase 4 kill criteria

- **External-user NPS < 20** after two iteration cycles on feedback. → Product-market fit is questionable; halt platform work, return to engine improvements.

### Phase 5 kill criteria

- **Multi-language quality < 70% of English baseline** across five tested languages. → Translation-preserving-timing is fundamentally fragile; deprioritize multi-language.

### Phase 6 kill criteria

- **Zero third-party domain packs** after 3 months of the SDK being available. → Ecosystem play has failed; refocus on direct-user product.

---

## 6. Cadence

- **Weekly:** Friday end-of-week demo + retrospective. Update `workflows/lessons.md`.
- **Phase-end:** Phase demo with all deliverables. Kill-criteria check. Go/no-go on next phase.
- **Quarterly:** Reassess roadmap against reality. Prune or re-order later-phase milestones.

---

## 7. What could make this go faster

- **More Opus credits** (not in scope — constraint is $0 API) — not available.
- **A second contributor** on Manim skills specifically — the skill library is the rate-limit on Phase 3+.
- **A curated dataset of reference videos** (3Blue1Brown, Khan, etc.) to train the `pedagogical-critique` rubric against — build during Phase 2.

---

## 8. What could make this go slower

- ElevenLabs API changes breaking the timestamp contract. *Mitigation:* pin client library, monitor release notes, fast fallback to WhisperX path from Phase 3.
- Claude model deprecations mid-phase. *Mitigation:* model defaults are in `config.yaml`, swap is a one-line change; regression suite catches regressions.
- Manim Community releases breaking patterns. *Mitigation:* pin `manim==0.19.x`; quarterly reassess.
- Single-dev burnout. *Mitigation:* weekly demos force scope discipline; kill criteria prevent sunk-cost spiral.
