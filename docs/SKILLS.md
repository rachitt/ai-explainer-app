# Pedagogica — Skills (Artifact 3)

Status: Phase 1 design. Cross-referenced with ARCHITECTURE.md.

Skills are where the knowledge lives. Agents are lean orchestrators; skills carry the craft. This document specifies the skill format, the full Phase 1 → Phase 6 inventory, which skills each agent loads, two worked examples (happy path + failed-compile retry), the authoring process, and the per-phase ship plan.

---

## 1. Philosophy

- **Agents are lean.** Each agent's `SKILL.md` (under `pedagogica/skills/agents/<name>/`) is ~100–300 lines of prose: role, input contract, output contract, decision heuristics, exit conditions. No domain knowledge embedded.
- **Knowledge lives in knowledge skills** (under `pedagogica/skills/knowledge/` and `pedagogica/skills/domains/`). Loaded on demand via the `load_skill(name)` tool exposed by Claude Code's skill system.
- **Skills are versioned, tested, diffable.** A skill's examples render (for Manim skills) or produce expected JSON (for pedagogy skills) as part of its test suite.
- **Skills compose.** A single Manim-code agent call may load: `scene-spec-schema`, `manim-primitives`, `manim-calculus-patterns`, `latex-for-video`, `scene-composition`. The agent decides what to load based on the scene's `required_skills` field from the Storyboard.
- **Cheap to author, expensive to promote to production.** Anyone can draft a skill. Merging it to `main` requires: passing tests, one rendered example reviewed, owner sign-off.

---

## 2. Skill format specification

Every skill is a directory. Minimum required file: `SKILL.md`.

```
pedagogica/skills/<category>/<skill_name>/
├── SKILL.md              # required
├── examples/             # optional; required for manim-* skills
│   ├── example_01.py     # for Manim skills, a runnable scene file
│   ├── example_01.mp4    # rendered artifact; committed for visual review
│   └── expected_output.json   # for pedagogy skills
├── rubric.yaml           # optional; required for *-critique skills
├── error_catalog.yaml    # optional; required for manim-debugging
├── schema.py             # optional; skills that define Pydantic models reference schemas/
└── tests/
    ├── test_examples_render.py   # for Manim skills
    └── test_skill_quality.py     # for pedagogy skills
```

### `SKILL.md` frontmatter

```yaml
---
name: manim-calculus-patterns
version: 0.3.1
category: manim                    # pedagogy | domain | narration | manim | audio | critique | orchestration
triggers:
  - domain:calculus
  - scene_type:math
requires:
  - scene-spec-schema@^1.0.0
  - manim-primitives@^1.0.0
  - latex-for-video@^0.2.0
token_estimate: 4200               # approximate tokens the body loads into context
tested_against_model: claude-opus-4-7
owner: rachit
last_reviewed: 2026-04-20
description: >
  Canonical patterns for animating calculus concepts: derivative-as-slope,
  Riemann sums, epsilon-delta limits, tangent tracker, related rates.
---
```

Frontmatter fields (strict — validated by `pedagogica-tools validate-skill`):

| Field | Required | Purpose |
|---|---|---|
| `name` | ✅ | Kebab-case identifier. Must match directory name. |
| `version` | ✅ | SemVer. Bump on any content change. |
| `category` | ✅ | Controls where it lives in the tree, and triggers routing. |
| `triggers` | ✅ | List of conditions under which an agent should auto-suggest loading this skill. |
| `requires` | ✅ | Other skills this skill references. Version ranges. |
| `token_estimate` | ✅ | Updated by CI on every merge. Used by cost-governor for budget. |
| `tested_against_model` | ✅ | Document which model this skill was validated with. |
| `owner` | ✅ | Single human responsible. Required reviewer on changes. |
| `last_reviewed` | ✅ | Date. Renewed on any non-trivial edit. |
| `description` | ✅ | One-paragraph summary. Used by `load_skill` indexers. |

### `SKILL.md` body structure

1. **Purpose** — one paragraph. What does this skill teach the agent to do?
2. **When to load** — rules of thumb for the agent consuming this skill.
3. **Core content** — the actual knowledge. Format varies by category:
   - *Pedagogy:* principles + decision heuristics + scaffolded examples.
   - *Domain:* curriculum map + canonical examples + notation conventions.
   - *Manim:* runnable code examples with commentary, common pitfalls, fixes.
   - *Critique:* rubric with scoring criteria and negative examples.
4. **Examples** — inline short ones; link to `examples/` for longer.
5. **Gotchas / anti-patterns** — what not to do.
6. **Changelog** — version bumps and why.

### Testing requirements per category

| Category | Tests required |
|---|---|
| `manim` | All examples render without error; visual review sign-off in PR. |
| `pedagogy` | `examples/expected_output.json` reproducible from a fixed prompt + model. |
| `domain` | Sample topics produce valid `CurriculumPlan` JSON. |
| `narration` | Readability metrics (Flesch-Kincaid, sentence length) within bounds. |
| `critique` | Rubric applied to seed fixtures produces expected scores. |
| `orchestration` | Integration test using the skill within a full job. |

No untested skill is loaded in production config.

---

## 3. Full skill inventory

Organized by the six categories. Phase column indicates when the skill ships. `*` = this skill is what makes Phase 1 Phase 1.

### 3.1 Pedagogy skills (`pedagogica/skills/knowledge/pedagogy-*`)

| Name | Phase | Purpose |
|---|---|---|
| `pedagogy-sequencing` * | 1 | Ordering concepts. When to introduce notation. Concrete-to-abstract progression rules. |
| `explanation-patterns` * | 1 | Templates: define → motivate → example → generalize; compare/contrast; first-principles build-up. |
| `pedagogy-cognitive-load` * | 1 | Chunking rules, pause placement, working-memory constraints. One new concept per 20–30s. |
| `pedagogy-misconceptions` | 2 | Catalog of common misconceptions per domain + preempt strategies. |
| `pedagogy-levels` | 2 | How explanations differ across elementary / highschool / undergrad / graduate. |
| `worked-example-design` | 2 | How to construct worked examples that transfer. Variation theory. |
| `interactive-beats` | 5 | Pause-and-think prompts, "try this yourself" moments, embedded questions. |

### 3.2 Domain packs (`pedagogica/skills/domains/domain-*`)

| Name | Phase | Purpose |
|---|---|---|
| `domain-calculus` * | 1 | Curriculum progression, canonical examples, notation. The only pack in Phase 1. |
| `domain-linear-algebra` | 3 | Vectors, matrices, eigen, basis changes. |
| `domain-probability-statistics` | 3 | Distributions, sampling, Bayesian updating. |
| `domain-classical-mechanics` | 3 | Newton, energy, oscillations. |
| `domain-electromagnetism` | 5 | Fields, Maxwell, circuits. |
| `domain-quantum-mechanics` | 5 | Wavefunctions, operators, measurement. |
| `domain-organic-chemistry` | 5 | Reactions, mechanisms, stereochemistry. |
| `domain-molecular-biology` | 5 | Pathways, replication, gene expression. |
| `domain-algorithms-data-structures` | 5 | Sorting, trees, graphs, complexity. |
| `domain-machine-learning` | 5 | Gradient descent, neural nets, regularization. |
| `domain-microeconomics` | 5 | Supply/demand, utility, market structures. |

### 3.3 Narration skills (`pedagogica/skills/knowledge/narration-*` and `tts-*`)

| Name | Phase | Purpose |
|---|---|---|
| `spoken-narration-style` * | 1 | Writing for the ear: sentence length, signposting, redundancy, breath points. |
| `tts-prompting-elevenlabs` * | 1 | ElevenLabs voice selection, model choice, stability/style settings, timestamp API. |
| `voice-direction` | 2 | Emotional tone, emphasis, pacing directives in ElevenLabs markup. |
| `spoken-narration-multilingual` | 5 | Per-language cadence and idiom. |
| `tts-prompting-openai` | 5 | OpenAI TTS when cost/latency matters. |
| `tts-prompting-kokoro` | 5 | Local Kokoro for zero-cost offline generation. |

### 3.4 Manim / rendering skills (`pedagogica/skills/knowledge/manim-*` and adjacent)

| Name | Phase | Purpose |
|---|---|---|
| `scene-spec-schema` * | 1 | Canonical Pydantic schema for `SceneSpec`. Loaded by every agent that touches scene specs. |
| `manim-primitives` * | 1 | Core: `Write`, `Create`, `Transform`, `MathTex`, `Axes`, `ValueTracker`. Runnable examples. |
| `manim-calculus-patterns` * | 1 | Derivative def, tangent tracker, Riemann sums, limit visualizations. |
| `manim-debugging` * | 1 | Error catalog + fixes. Loaded only on retry path, not first-pass. |
| `latex-for-video` * | 1 | Sizing, color-coded terms, `\underbrace`, aligned transformations. |
| `scene-composition` * | 1 | Layout, framing, reading order, split-screen rules. |
| `color-and-typography` * | 1 | Default palette, semantic colors, font stack. Phase 1 = one preset. |
| `transition-vocabulary` | 2 | Fade, morph, camera sweep — when to use which. |
| `manim-linalg-patterns` | 3 | Vector addition, matrix transformations, eigenvector animations. |
| `manim-probability-patterns` | 3 | Distributions, sampling, Bayesian updating. |
| `manim-physics-patterns` | 3 | Projectile motion, wave superposition, field visualizations. |
| `manim-algorithms-patterns` | 5 | Sorting, tree traversals, graph algorithms. |
| `manim-code-viz` | 5 | Syntax-highlighted code display, execution stepping. |
| `manim-data-viz` | 5 | CSV → animated charts. |
| `manim-3d` | 5 | ManimGL 3D scenes, camera control. |
| `handwriting-synthesis` | 6 | Optional real-handwriting mode. |

### 3.5 Audio skills (`pedagogica/skills/knowledge/audio-*`)

| Name | Phase | Purpose |
|---|---|---|
| `audio-visual-sync` * | 1 | Alignment logic; the trickiest skill. Used by Sync agent. |
| `pacing-rules` * | 1 | Pause placement, tempo variation, breath points. |
| `music-bed-selection` | 5 | Tone matching, ducking during narration. |
| `sound-design` | 5 | Tasteful SFX for emphasis (whooshes, dings). |

### 3.6 Critique skills (`pedagogica/skills/knowledge/*-critique` and `*-verification`)

| Name | Phase | Purpose |
|---|---|---|
| `pedagogical-critique` * | 1 | Rubric for evaluating explanation quality. Phase 1: report-only. |
| `visual-critique` | 2 | Rubric for composition, readability, coherence. |
| `factual-verification-math` | 2 | Checks identities via SymPy. |
| `factual-verification-science` | 3 | Checks claims; references sources. |
| `accessibility-rubric` | 3 | Contrast, caption accuracy, reading speed, alt descriptions. |

### 3.7 Orchestration skills (`pedagogica/skills/knowledge/orchestration-*`)

| Name | Phase | Purpose |
|---|---|---|
| `retry-strategy` * | 1 | When to retry, when to escalate model, when to give up. |
| `cost-routing` * | 1 | Model selection rules (Opus/Sonnet/Haiku per agent tier). |
| `budget-governance` * | 1 | Graceful degradation when budget near limit. |

### Phase 1 skill count

Counting the `*` entries: **15 knowledge skills + 1 domain pack (calculus) + ~14 agent skills = 30 skills to ship in Phase 1.** Tight but achievable. Everything else is deferred with full inventory here so the shape is known.

---

## 4. Agent-to-skill mapping

For each Phase-1 agent: always-loaded skills vs. conditionally-loaded. "Conditional" means the agent decides per input whether to load based on triggers.

Model column shows default; may escalate per `retry-strategy`.

### Planning tier

| Agent | Model | Always loads | Conditional |
|---|---|---|---|
| **Intake** | Haiku 4.5 | `scene-spec-schema` | — |
| **Curriculum** | Sonnet 4.6 | `pedagogy-sequencing`, `explanation-patterns`, `pedagogy-cognitive-load`, `domain-calculus` | — |
| **Storyboard** | Sonnet 4.6 | `pedagogy-sequencing`, `pedagogy-cognitive-load`, `scene-composition`, `transition-vocabulary` | `domain-<N>` based on intake |

### Script tier

| Agent | Model | Always loads | Conditional |
|---|---|---|---|
| **Script** | Sonnet 4.6 | `spoken-narration-style`, `pacing-rules` | `domain-<N>` for terminology |
| **Script Critic** | Sonnet 4.6 | `spoken-narration-style`, `pedagogical-critique` | `domain-<N>` for fact checks |

### Visual tier

| Agent | Model | Always loads | Conditional |
|---|---|---|---|
| **Visual Planner** | Sonnet 4.6 | `scene-spec-schema`, `scene-composition`, `color-and-typography` | `manim-<domain>-patterns` based on scene beat type |
| **Layout** | Sonnet 4.6 | `scene-spec-schema`, `scene-composition` | — |
| **Manim Code** | **Opus 4.7** | `scene-spec-schema`, `manim-primitives`, `latex-for-video` | `manim-calculus-patterns`, other `manim-<domain>-patterns`, `color-and-typography` |
| **Manim Repair** | Sonnet 4.6 (→ Opus 4.7 on escalation) | `manim-debugging`, `manim-primitives` | skill pack that was loaded on the original failing call |

### Audio tier

| Agent | Model | Always loads | Conditional |
|---|---|---|---|
| **TTS** | — (no LLM; direct HTTP) | `tts-prompting-elevenlabs` as a config doc | — |
| **Sync** | Sonnet 4.6 | `audio-visual-sync`, `pacing-rules`, `scene-spec-schema` | — |

### Assembly tier

| Agent | Model | Always loads | Conditional |
|---|---|---|---|
| **Editor** | — (no LLM; FFmpeg) | none | — |
| **Subtitle** | — (pure function) | none | — |

### Quality tier

| Agent | Model | Always loads | Conditional |
|---|---|---|---|
| **Pedagogical Critic** | Sonnet 4.6 | `pedagogical-critique`, `pedagogy-sequencing`, `explanation-patterns` | `domain-<N>` |

### Meta tier

| Agent | Model | Always loads | Conditional |
|---|---|---|---|
| **Orchestrator** | Sonnet 4.6 | `retry-strategy`, `cost-routing`, `budget-governance`, `scene-spec-schema` | — |
| **Cost Governor** | Haiku 4.5 | `budget-governance` | — |

### Why Opus only for Manim Code

The Manim code agent is the single most reasoning-intensive call — it must produce ~100–400 lines of working Python that respects positioning, timing, math rendering, and scene composition all at once. Everything else in Phase 1 can run on Sonnet. Opus usage is bounded to one call per scene (plus retry escalations), so prompt-cache hit rate on the stable preamble (skill content) is high.

---

## 5. Worked examples

### 5.1 Happy path — calculus scene rendering

User: `/pedagogica generate "explain derivative as slope of tangent line"`

```
[orchestrator loads: retry-strategy, cost-routing, budget-governance, scene-spec-schema]

[intake  — Haiku]
  loads: scene-spec-schema
  → 01_intake.json  (domain=calculus, level=undergrad, length=180s)

[curriculum — Sonnet]
  loads: pedagogy-sequencing, explanation-patterns, pedagogy-cognitive-load, domain-calculus
  → 02_curriculum.json  (3 LOs, 0 misconceptions preempted in P1)

[storyboard — Sonnet]
  loads: pedagogy-sequencing, pedagogy-cognitive-load, scene-composition,
         transition-vocabulary, domain-calculus
  → 03_storyboard.json  (5 scenes, ~36s each)

for scene_01 (beat: hook, intent: "curve with secant line becoming tangent")
  [script — Sonnet]
    loads: spoken-narration-style, pacing-rules, domain-calculus
    → scenes/scene_01/script.json  (~55 words, 3 markers)
  [visual-planner — Sonnet]
    loads: scene-spec-schema, scene-composition, color-and-typography,
           manim-calculus-patterns   ← triggered by scene beat
    → scenes/scene_01/spec.json
  [layout — Sonnet]
    loads: scene-spec-schema, scene-composition
    → scenes/scene_01/placements.json
  [manim-code — OPUS]
    loads: scene-spec-schema, manim-primitives, latex-for-video,
           manim-calculus-patterns, color-and-typography
    → scenes/scene_01/code.py
  [compile — subprocess, sandbox-exec]
    → scenes/scene_01/render.mp4   ✓ first-pass success
    trace append: manim_render { attempt: 1, success: true, duration: 4.2s }
  [tts — HTTP to ElevenLabs]
    returns audio mp3 + word timings
    → scenes/scene_01/tts.mp3, timing.json
    char_count: 285 → cost_governor: $0.057 accrued
  [sync — Sonnet]
    loads: audio-visual-sync, pacing-rules, scene-spec-schema
    → scenes/scene_01/sync.json  (drift: 0.08s, within budget)
  (Phase 1 does NOT re-emit code based on sync — code.py & render.mp4 are final)

(repeat for scenes 02–05)

[editor — FFmpeg via bash]
  → final.mp4  (180s, 720p, 30fps, h264, aac audio)

[subtitle — pure function]
  → final.vtt

[pedagogical-critic — Sonnet, REPORT ONLY]
  loads: pedagogical-critique, pedagogy-sequencing, explanation-patterns, domain-calculus
  → critique.json  (overall: 4.2/5, suggestions for P2 regen)

[orchestrator — finalizes]
  job_state.terminal = true
  total wall-clock: 7m 22s
  total ElevenLabs cost: $0.34
  total LLM tokens: 184k input (92% cache-read), 14k output
```

Claude Code transcript shows every step. `trace.jsonl` captures all 43 events. `pedagogica-tools view <job_id>` prints the timeline.

### 5.2 Failure path — Manim compile error triggers repair loop

In scene_03 (beat: example, intent: Riemann sum approximation of area):

```
[manim-code — OPUS]
  loads: scene-spec-schema, manim-primitives, latex-for-video,
         manim-calculus-patterns, color-and-typography
  → scenes/scene_03/code.py  (attempt 1)

[compile — subprocess]
  stderr: "ValueError: Cannot call .get_graph() on Axes without specifying x_range and y_range"
  error_classification: geometry_error
  → scenes/scene_03/compile_attempt_1.json  (success: false)

[retry-strategy decides: attempt 2, Sonnet 4.6 with error+40 source lines]

[manim-repair — Sonnet]
  loads: manim-debugging, manim-primitives, manim-calculus-patterns (same pack as attempt 1)
  input: code.py + stderr + 40-line window around the error
  → scenes/scene_03/code.py  (attempt 2, modified)

[compile — subprocess]
  stderr: "LaTeX Error: File 'xcolor.sty' not found" (different error)
  error_classification: latex_error

[retry-strategy decides: attempt 3, Opus 4.7 with full file + error catalog]

[manim-repair — OPUS]
  loads: manim-debugging (full error catalog mode), manim-primitives,
         manim-calculus-patterns, latex-for-video
  → scenes/scene_03/code.py  (attempt 3, replaces xcolor usage with inline color args)

[compile — subprocess]
  success, 5.1s
  → scenes/scene_03/render.mp4

trace shows: 3 compile events, 2 manim_repair events, error classifications logged,
skill versions pinned for the successful attempt
```

Skill evolution hooked in: the failure mode (`LaTeX Error: File 'xcolor.sty' not found`) triggers a review. If it recurs, `manim-debugging`'s error catalog gets a new entry, its example pack gets a new positive example (inline color args instead of xcolor), and version bumps. The cache is invalidated for this input hash; the next run of the regression suite exercises the new pattern.

---

## 6. Skill authoring guide (outline for `pedagogica/skills/AUTHORING.md`)

This outline will be the actual content of `pedagogica/skills/AUTHORING.md` when we create it in Phase 1 week 1.

### Sections

1. **Purpose of this guide** — how to write a skill that helps the agent, not just the human reading it.
2. **The three skill archetypes** — knowledge (principles + heuristics), pattern library (examples + variations), reference (lookups + catalogs). Know which you're writing.
3. **Frontmatter requirements** — exact field list, validation rules.
4. **Writing for the ear of an LLM** — prefer imperative mood; short paragraphs; explicit scoping ("when X, do Y"); avoid hedging that blurs decisions.
5. **Examples are first-class** — every example must be runnable (Manim) or reproducible (pedagogy). Include negative examples for anti-patterns.
6. **Testing discipline**:
   - Manim skills: `tests/test_examples_render.py` renders each example to MP4 and asserts frame count > 0.
   - Pedagogy skills: `tests/test_skill_quality.py` feeds a fixed input through the relevant agent with only this skill + schema loaded and diffs output against `examples/expected_output.json`.
   - Critique skills: `tests/test_rubric_fixtures.py` applies rubric to seed fixtures.
7. **Version bumping** — patch for typos / clarifications, minor for new examples or heuristics, major for incompatible restructuring.
8. **PR checklist** — tests pass, example reviewed visually (for Manim), token estimate updated, changelog entry added, owner sign-off, `last_reviewed` updated.
9. **Deprecation** — how to retire a skill, how to migrate dependents, the `DEPRECATED.md` index.
10. **Anti-patterns** — skills that do too much, skills that duplicate other skills, skills that bake in information that should come from inputs.

### Review ownership

- `manim-*` skills: any Phase-1 contributor with a merged Manim skill prior.
- `domain-*` packs: the owner field is load-bearing — a domain pack without an identified owner is not promoted to production config.
- `critique` skills: owner + one second reviewer from outside the owner's usual area.

### Hot-swap rule

In dev mode (`PEDAGOGICA_DEV=1`), skills are loaded from the working directory, not the version-pinned copy. A save + re-run hits the changes. In production config (default), skills are pinned to the versions listed in `config.yaml`; changes require a config bump.

---

## 7. Skill phase allocation

### Phase 1 (weeks 1–6) — calculus, CLI only

**Ship:**
- All 14 Phase-1 agent skills.
- All 15 starred (`*`) knowledge skills.
- `domain-calculus`.

**Do not ship:**
- Any `pedagogy-misconceptions`, `pedagogy-levels`, `worked-example-design`.
- Visual Critic, Factual Verifier, Accessibility Auditor (agents).
- All `voice-direction`, all non-ElevenLabs TTS skills.
- All non-calculus domain packs, all non-calculus `manim-*-patterns`.
- Any music / SFX skills.

Intentionally small surface. Makes the Phase-1 regression suite feasible.

### Phase 2 (weeks 7–12) — quality, full critic tier

**Add:**
- `pedagogy-misconceptions`, `pedagogy-levels`, `worked-example-design`.
- `visual-critique`, `factual-verification-math`.
- `voice-direction`.
- `transition-vocabulary`.
- Agent: Visual Critic, Factual Verifier.
- Scene-level regeneration loop wired from critics.
- Expand `manim-calculus-patterns` from ~10 to ~40 patterns via examples.

### Phase 3 (weeks 13–20) — multi-domain

**Add:**
- `domain-linear-algebra`, `domain-probability-statistics`, `domain-classical-mechanics`.
- `manim-linalg-patterns`, `manim-probability-patterns`, `manim-physics-patterns`.
- `factual-verification-science`, `accessibility-rubric`.
- Agent: Accessibility Auditor.
- Alignment agent with WhisperX (enables non-ElevenLabs TTS).
- Audio Post agent.

### Phase 4 (weeks 21–30) — web platform

No new skills; consolidation. Skill-loading semantics gain a skill-registry API.

### Phase 5 (weeks 31–40) — scale

**Add:**
- All remaining domain packs + `manim-*-patterns`.
- `interactive-beats`, `spoken-narration-multilingual`.
- All non-ElevenLabs TTS skills.
- `manim-code-viz`, `manim-data-viz`, `manim-3d`.
- `music-bed-selection`, `sound-design`.

### Phase 6 — platform and ecosystem

**Add:**
- `handwriting-synthesis`.
- Third-party skill pack manifest format + marketplace scaffolding.

---

## 8. Skill telemetry we track

Per job (in `trace.jsonl`):
- Every skill load: name, version, token count, which agent loaded it.
- Per skill version: load count, average tokens, correlation with compile success / critic score.

Per skill (aggregated in regression runs):
- Load frequency over time.
- Correlation with success: did scenes where this skill loaded produce better videos?
- Staleness: when was it last reviewed, when was it last loaded.

Insights feed back into skill authoring — e.g., if `manim-calculus-patterns@0.3.1` is loaded 100× but correlates with 62% first-pass compile success while `@0.4.0` correlates with 89%, we deprecate `0.3.1`.

---

## 9. What is NOT a skill

Things that live elsewhere, deliberately:

- **Pydantic schemas** — live in `schemas/src/pedagogica_schemas/`. Skills reference them but don't own them; breaking a schema is a repo-wide change, not a skill bump.
- **Python helpers** (Manim render, FFmpeg, ElevenLabs client) — live in `tools/`. They encode execution logic, not knowledge.
- **Agent system prompts** — Phase 1 these are inline in each agent's `SKILL.md`. Phase 4 extracts them to `pedagogica/prompts/` as versioned `.md` files.
- **Configuration** — model defaults, budget caps, feature flags — live in `config.yaml` at repo root. Skills should not hard-code config.

The distinction: skills are prose that guides reasoning. Code is execution. Schemas are contracts. Config is operational.
