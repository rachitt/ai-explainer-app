# Pedagogica — Risks (Artifact 5)

Status: Phase 1 risk register. Reviewed against ARCHITECTURE.md and ROADMAP.md.

> **Renderer update (2026-04-21):** R1 ("LLMs can't reliably generate Manim code") is now about chalk, not MCE, per ADR 0001. The kill criteria specific to the chalk bet live in the ADR (K1–K5) and supplement R1. New risk: chalk is a single-author library with bus factor 1 — mitigation is strict typing, 100% core-test coverage target, and ADRs for each primitive added. See `docs/CHALK_ROADMAP.md` for scope.

Top 10 risks ordered by severity × likelihood. Each has a description, early-warning signal, mitigation, and fallback plan. A risk appears here only if it can materially alter the roadmap.

Severity scale: `S1` existential (project cannot ship) / `S2` major (phase slips ≥ 3 weeks) / `S3` moderate (feature quality compromised).
Likelihood: `L1` expected / `L2` plausible / `L3` possible-but-unlikely.

---

## R1 — Manim code generation unreliability (S1 × L1)

**Description.** The core architectural bet is that LLMs can reliably produce working Manim code for pedagogical scenes. If first-pass compile success is too low and repair loops don't converge, every downstream metric (wall-clock, cost, watchable rate) collapses. Manim is unusually punishing — it combines Python, LaTeX, scene composition, timing, and a mental model that changes across versions.

**Early-warning signals.**
- Week 3 first-pass compile < 30% across 30 scene specs.
- Repair loop diverges (attempt 2 fixes the original error but introduces a new class of error).
- Error classifications cluster on one axis (e.g., 80% LaTeX) — signals a skill gap, not a pipeline problem.
- Token usage per scene creeps past 25k output tokens — indicates the model is flailing.

**Mitigation.**
- Heavy investment in `manim-primitives` and `manim-calculus-patterns` examples in weeks 1–3 — every example counts.
- `manim-debugging` error catalog grows from every failure, not just catastrophic ones.
- `scene-spec-schema` is tightened over time so the Visual Planner produces progressively less-ambiguous specs.
- Opus 4.7 reserved specifically for this call. Cache preamble aggressively.

**Fallback.**
- **Tier-1 fallback:** Narrow the scene DSL until Manim-code becomes template-fill rather than freeform codegen. Agent selects from ~30 templated scene types and parameterizes them. Reduces expressiveness; stabilizes output.
- **Tier-2 fallback:** Hand-authored Manim "snippet library" — agent composes scenes from vetted snippets rather than writing Python. Essentially a domain-specific language above Manim.
- **Tier-3 fallback (kill):** Project is infeasible with LLM codegen; pivot to a template-only editor product.

---

## R2 — Audio-visual sync drift (S1 × L2)

**Description.** Manim `run_time` intent rarely matches TTS reality. Drift accumulates across a scene. Beyond ~0.3s word-to-animation drift, the illusion of "the thing being drawn as it's spoken" dies — and with it, the 3B1B comparison.

**Early-warning signals.**
- Week 4 drift > 0.3s on > 25% of marker-anchored animations.
- ElevenLabs timestamps have systematic gaps at boundaries or silences.
- Scene-level duration from Manim vs. audio vary by > 20% after sync — indicates the visual planner's rate estimates are miscalibrated.

**Mitigation.**
- Sync agent reemits `code.py` with measured run_times after TTS, rather than predicting. This is the "measure twice, render once" approach.
- Visual-planner rate constants are calibrated against actual render-and-measure data from Phase 1 week 2's 30-scene batch.
- Padding strategy is always audio-authoritative: if animation is short, extend `wait()`; if audio is short, pad silence at end — never truncate the measured reality.

**Fallback.**
- **Tier-1:** Audio as source of truth — animation timings derived from TTS word timings only; visual-planner's `run_time` becomes advisory.
- **Tier-2:** Reduce scene beats to 3–5 per video; longer scenes with smoother, less-tightly-synced animations. Accept less-precise beat alignment.
- **Tier-3:** Switch to post-production sync — render animations without fixed durations, then stretch or speed up to match audio (quality hit on geometry accuracy).

---

## R3 — Pedagogical quality plateau (S2 × L2)

**Description.** Pipeline runs reliably, videos are watchable on a rubric, but they feel lifeless, generic, textbook-summary-ish. 3B1B-caliber explanations depend on insight and motivation that may not emerge from even a well-orchestrated agent pipeline. We produce "AI-generated explainer videos" rather than "good explainer videos."

**Early-warning signals.**
- Phase 1 critic scores clustered at 3.5–3.8 out of 5 despite all pipeline fixes.
- Side-by-side comparisons with 3B1B/Khan look like "obvious AI vs. human" — pacing, choice of example, visual metaphor all feel off.
- External reviewers (Phase 4) can pick Pedagogica videos out of a mix at > 80% accuracy.

**Mitigation.**
- Invest in `explanation-patterns` and `pedagogy-misconceptions` skills explicitly — these carry the craft.
- Seed `domain-calculus` with *worked* canonical explanations (with commentary on why they're good), not just topic lists.
- Phase 2 critic loop pushes quality from pass/fail rubric to directional feedback.
- Phase 4 user feedback is the real signal; aggregate which scene types get regenerated, study failure patterns.

**Fallback.**
- **Tier-1:** Accept a quality ceiling below 3B1B; position as "Khan Academy throughput, 3B1B aspiration." Grow the skill library for years to close the gap.
- **Tier-2:** Invest in a human-in-the-loop editorial step in Phase 4 (creator reviews and marks scenes for regen with prose feedback).

---

## R4 — Hallucinated math/science facts (S1 × L2)

**Description.** Generated videos confidently state things that are wrong — a formula mis-transcribed, a definition subtly off, a theorem applied outside its hypotheses. In education this is worse than in most LLM applications: users consume it as fact and build further learning on top.

**Early-warning signals.**
- Phase 1 regression review catches factual errors in > 5% of topics.
- Any factual error in a "high-stakes" domain (medicine, law, finance) — we don't target these but users may use the tool for them.
- Formula transcription errors in `MathTex` calls (visual) not caught because the speaker's narration was correct.

**Mitigation.**
- `factual-verification-math` (Phase 2) uses SymPy to verify identities in Script and SceneSpec. Any claim of the form "X = Y" is checked.
- `factual-verification-science` (Phase 3) cross-references claims against a grounded source.
- Visual-audio factual checker: compare LaTeX in SceneSpec against narration text. Divergence = flag.
- `manim-code` is instructed to emit identical LaTeX as the Script references, not re-derive.

**Fallback.**
- **Tier-1:** All videos carry a visible disclaimer ("AI-generated, verify before trusting") through Phase 5.
- **Tier-2:** Domain-pack owners hand-curate a "verified claims" list; agent must cite from this list, not generate.
- **Tier-3:** Factual-verifier becomes blocking (not just reporting); lower reliability for higher correctness.

---

## R5 — Cost overruns (S2 × L2)

**Description.** Phase 1 runs on Rachit's Claude Code subscription ($0 API), but ElevenLabs is paid. Later phases require Anthropic API billing. Per-video cost escalates unpredictably when repair loops trigger, critic-driven regeneration fires, and long videos emerge. The $3 / 3-min target by v3 is ambitious; misses compound.

**Early-warning signals.**
- Phase 1 ElevenLabs cost > $15 per 10-min video (kill-criteria trigger).
- Repair loops average > 2 attempts per failing scene — blows up cached-token benefit.
- Phase 4 cloud LLM budget burn rate > projections by > 2×.

**Mitigation.**
- `budget-governance` skill enforces hard per-job cap from day 1. Override flag for dev, hard stop in prod.
- `cost-routing` skill matches model to agent (Opus only where it earns its cost).
- Content-hash LLM cache from day 1 — replays are free.
- Regression suite surfaces cost regressions per merge.

**Fallback.**
- **Tier-1:** Auto-downgrade Opus → Sonnet → Haiku when budget is ≥ 80% consumed. Accept quality degradation.
- **Tier-2:** Pre-render a "static" opener/closer once and cache across videos.
- **Tier-3:** Cost-sensitive voice selection — cheaper ElevenLabs voices for drafts, premium for finals.

---

## R6 — TTS quality ceiling for education (S2 × L2)

**Description.** ElevenLabs is excellent but still has a noticeable "AI voice" texture, occasional mispronunciations of technical terms, and uncanny valley on extended speech. For educational content where listeners spend 10+ minutes, fatigue is real. Quality has been improving steadily but may plateau.

**Early-warning signals.**
- Users in Phase 4 beta report "sounds AI" as #1 complaint.
- Domain-specific mispronunciations cluster (e.g., "Riemann" wrong every time).
- Intonation errors on questions / emphasis beats.

**Mitigation.**
- `tts-prompting-elevenlabs` skill accrues per-term pronunciation overrides using IPA or phonetic hints.
- `voice-direction` skill (Phase 2) adds emphasis markup per-sentence.
- Custom voice clones (Phase 5) where creator signs off on their own voice being used.

**Fallback.**
- **Tier-1:** Offer multiple voice options; let users pick the one they tolerate.
- **Tier-2:** Add natural pauses and breath points to disrupt the monotony.
- **Tier-3:** Multi-voice dialogue (Phase 5) to break up single-voice fatigue.

---

## R7 — Sandbox escape (S1 × L3)

**Description.** The Manim code agent is an LLM. Its output is executed code. A compromised or prompt-injected output could attempt network exfiltration, filesystem writes, or escape the sandbox. On a dev Mac with user credentials in home directory, blast radius is total.

**Early-warning signals.**
- `sandbox_violation` events in `trace.jsonl`.
- Unexpected network connections during a render (monitored via `sandbox-exec` profile denial logs).
- Generated code that imports non-Manim packages, hits filesystem outside the artifact dir, or spawns subprocesses.

**Mitigation.**
- `sandbox-exec` profile denies network and writes outside `$ARTIFACTS_DIR/scenes/scene_NN/`.
- Resource limits enforced via wrapper (CPU 300s, wall 300s, memory 4 GB, output 500 MB).
- Static check before execution: grep generated code for `os.system`, `subprocess`, `socket`, `urllib`, `requests`, `open('/'...)`. Reject if present.
- In production (Phase 4), Firecracker microVMs with no network and ephemeral root FS.

**Fallback.**
- **Tier-1:** If `sandbox-exec` shows a gap, switch dev to Docker container immediately (memory hit acceptable for security).
- **Tier-2:** Any actual escape → pause all runs, audit, isolate the prompt that caused it, add to the static-check blocklist.
- **Tier-3:** Accept that "AI-generated code execution" has inherent risk; require explicit per-session opt-in for users running outside a clean environment.

---

## R8 — Scope creep (S2 × L1)

**Description.** The end-state product surface (Multi-language, series, voice cloning, marketplace, interactive elements, 3D, data viz, code execution) is vast. Each is a real feature someone will ask for. Without discipline, Phase 1 grows from 6 weeks to 6 months and the tracer bullet never ships.

**Early-warning signals.**
- Any week in Phase 1 where scope grows week-over-week.
- PRs that add features outside the phase's milestone scope.
- Roadmap items jumping phases.

**Mitigation.**
- NON_GOALS.md (Artifact 6) explicitly lists what's excluded; reviewed at every phase boundary.
- Kill criteria + phase gates (ROADMAP §5) force "ship or kill" decisions at 6-week cadence.
- Weekly demo discipline — if it can't be demoed, it didn't ship.
- `workflows/lessons.md` records scope-creep moments so patterns are caught.

**Fallback.**
- **Tier-1:** Extend the phase by up to 50% if scope creep is real work that adds value. Document in retrospective why.
- **Tier-2:** Cut phase scope to the original 6 weeks, defer the creep-work to its natural phase.
- **Tier-3:** Abandon a later-phase milestone to pay for an earlier-phase overshoot.

---

## R9 — Manim ecosystem changes (S2 × L3)

**Description.** Manim Community is volunteer-driven. A 0.20.x release could break skill examples, API changes could invalidate `manim-primitives`, maintainer turnover could stall the project. Our dependency on a particular version and style is load-bearing.

**Early-warning signals.**
- Manim Community release notes flag breaking changes.
- CI starts failing after dependency refresh.
- Upstream issue tracker shows sustained maintainer absence.

**Mitigation.**
- Pin `manim==0.19.x` in `pyproject.toml`. Quarterly reassess.
- All skill examples run in CI; breaking upstream changes show up on next refresh PR before merge.
- Fork-ready: maintain a clean dependency tree so we can fork Manim if needed (Apache-compatible license).

**Fallback.**
- **Tier-1:** Stay on a pinned version indefinitely; backport critical security fixes.
- **Tier-2:** Fork Manim Community, take on maintenance cost.
- **Tier-3:** Migrate to alternate renderer (custom SVG → video pipeline, or ManimGL). Major disruption; likely phase pivot.

---

## R10 — Solo dev burnout (S2 × L2)

**Description.** Phase 1 is 6 weeks solo, but the full roadmap is 40+ weeks. Parallel worktree workflow helps, but the sheer surface area is taxing. Burnout manifests as declining quality, missed regression runs, skipped retrospectives.

**Early-warning signals.**
- Two consecutive weeks without a Friday demo.
- `workflows/lessons.md` stops being appended.
- PRs merged without passing regression.
- Personal: sleep, mood, exercise regressions.

**Mitigation.**
- Weekly demo is mandatory — not aspirational. No demo = pause-and-reflect-week, not "extend into next week."
- Kill criteria exist for a reason. Killing a phase is a recovery mechanism.
- Phase-end retrospective is a real gate — skipping it is the strongest burnout signal.
- A second contributor on Manim skills would unblock Phase 3 significantly; pursue when funded.

**Fallback.**
- **Tier-1:** Insert a 1-week slack week between phases. Recharge; no deliverables.
- **Tier-2:** Cut scope on the current phase aggressively; ship the 50% that matters and archive the rest.
- **Tier-3:** Open-source earlier than planned (Phase 4 instead of 6) to attract contributors. Earlier OSS means more community support, less solo load.

---

## Risk summary table

| # | Risk | Severity | Likelihood | Phase most affected |
|---|---|---|---|---|
| R1 | Manim codegen unreliability | S1 | L1 | Phase 1 |
| R2 | Audio-visual sync drift | S1 | L2 | Phase 1 |
| R3 | Pedagogical quality plateau | S2 | L2 | Phase 2+ |
| R4 | Hallucinated facts | S1 | L2 | Phase 3+ |
| R5 | Cost overruns | S2 | L2 | Phase 4 |
| R6 | TTS quality ceiling | S2 | L2 | Phase 4+ |
| R7 | Sandbox escape | S1 | L3 | All |
| R8 | Scope creep | S2 | L1 | Every phase |
| R9 | Manim ecosystem changes | S2 | L3 | Phase 3+ |
| R10 | Solo dev burnout | S2 | L2 | Phase 2+ |

---

## Risks we are deliberately not tracking

- **Anthropic API pricing changes** — Phase 1 is on Claude Code subscription, so insensitive. Phase 4+ exposure, but cost is hedged by model-tier routing and cache.
- **AWS/GCP regional outages** — Phase 1 is local-only; Phase 4 picks multi-region when it matters.
- **Copyright claims on generated content** — output is generative, not reproducing copyrighted work. If a user prompts "recreate 3B1B's linear algebra series," that's their risk.
- **GDPR / FERPA compliance** — no user data collected in Phases 1–3. Addressed at Phase 6 enterprise features.

These may become risks in later phases; re-evaluated at phase boundaries.
